import json
import os
import socket
import subprocess
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
RUN_INTEGRATION = os.environ.get("RUN_DOCKER_INTEGRATION") == "1"


def _free_ports(count: int) -> list[int]:
    sockets = [socket.socket() for _ in range(count)]
    try:
        for sock in sockets:
            sock.bind(("127.0.0.1", 0))
        return [int(sock.getsockname()[1]) for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


@unittest.skipUnless(
    RUN_INTEGRATION,
    "Set RUN_DOCKER_INTEGRATION=1 to run the real Docker Compose test.",
)
class DockerComposeEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project = f"url-shortner-it-{uuid.uuid4().hex[:10]}"
        cls.environment = os.environ.copy()
        api_port, cassandra_port, redis_port, cache_port = _free_ports(4)
        cls.environment.update(
            {
                "API_PORT": str(api_port),
                "CASSANDRA_HOST_PORT": str(cassandra_port),
                "REDIS_HOST_PORT": str(redis_port),
                "URL_CACHE_REDIS_HOST_PORT": str(cache_port),
                "CASSANDRA_USERNAME": "integration",
                "CASSANDRA_PASSWORD": "integration-test-only",
                "SHORT_CODE_SECRET_KEY": uuid.uuid4().hex + uuid.uuid4().hex,
            }
        )
        cls.base_url = f"http://127.0.0.1:{cls.environment['API_PORT']}"
        cls.compose = [
            "docker",
            "compose",
            "--project-name",
            cls.project,
        ]
        try:
            cls._compose("up", "--build", "--detach", "--scale", "api=2")
            cls._wait_for_api()
        except Exception:
            cls._compose("logs", "--no-color", check=False)
            cls._cleanup()
            raise
        cls.addClassCleanup(cls._cleanup)

    @classmethod
    def _compose(cls, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            [*cls.compose, *arguments],
            cwd=ROOT,
            env=cls.environment,
            check=check,
            capture_output=True,
            text=True,
            timeout=900,
        )

    @classmethod
    def _wait_for_api(cls) -> None:
        deadline = time.monotonic() + 420
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                with urlopen(f"{cls.base_url}/openapi.json", timeout=3) as response:
                    if response.status == 200:
                        return
            except HTTPError as error:
                error.close()
                last_error = error
                time.sleep(3)
            except (OSError, URLError) as error:
                last_error = error
                time.sleep(3)
        raise TimeoutError(f"Compose API did not become ready: {last_error}")

    @classmethod
    def _cleanup(cls) -> None:
        cls._compose("down", "--volumes", "--remove-orphans", check=False)

    def test_load_balancer_replicas_cache_and_atomic_counter(self) -> None:
        replica_ids = self._compose("ps", "--quiet", "api").stdout.splitlines()
        self.assertEqual(len(replica_ids), 2, "Expected two running API replicas")

        urls = [
            f"https://example.com/integration/{index}"
            for index in range(16)
        ]
        with ThreadPoolExecutor(max_workers=8) as executor:
            responses = list(executor.map(self._create_short_url, urls))

        short_codes = [item["short_code"] for item in responses]
        self.assertEqual(len(set(short_codes)), len(urls))
        self.assertTrue(all(item["target_url"] in urls for item in responses))

        listed = self._request("GET", "/api/url-shortner/")
        self.assertEqual(len(listed), len(urls))

        code = short_codes[0]
        for _ in range(5):
            fetched = self._request("GET", f"/api/url-shortner/{code}")
            self.assertEqual(fetched["short_code"], code)

        cache_exists = self._compose(
            "exec",
            "-T",
            "url-cache-redis",
            "redis-cli",
            "EXISTS",
            f"url-shortner:cache:{code}",
        ).stdout.strip()
        self.assertEqual(cache_exists, "1", "Hot URL was not promoted to cache")

        counter_value = self._compose(
            "exec",
            "-T",
            "redis",
            "redis-cli",
            "GET",
            "url_shortner:short_code:sequence",
        ).stdout.strip()
        self.assertEqual(int(counter_value), 62**3 - 1 + len(urls))

        logs = [
            subprocess.run(
                ["docker", "logs", replica_id],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            ).stdout
            for replica_id in replica_ids
        ]
        self.assertTrue(
            all("/api/url-shortner/new" in log for log in logs),
            "Requests were not observed on every API replica through Nginx",
        )

    def _create_short_url(self, target_url: str) -> dict:
        return self._request(
            "POST",
            "/api/url-shortner/new",
            {"target_url": target_url},
        )

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=20) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read())
