import unittest

from hashids import Hashids

from src.infrastructure.services.redis_hashids_short_code_generator import (
    RedisHashidsShortCodeGenerator,
)


class InMemoryRedis:
    def __init__(self) -> None:
        self.value: int | None = None

    async def eval(self, script: str, numkeys: int, key: str, minimum: int) -> int:
        if self.value is None or self.value < minimum:
            self.value = minimum
        return self.value

    async def incr(self, key: str) -> int:
        self.value = (self.value or 0) + 1
        return self.value


class RedisHashidsShortCodeGeneratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_initializes_counter_and_generates_decodable_unique_codes(self) -> None:
        redis = InMemoryRedis()
        generator = RedisHashidsShortCodeGenerator(redis, "test-secret")
        await generator.initialize()

        first = await generator.generate()
        second = await generator.generate()
        hashids = Hashids(
            salt="test-secret",
            min_length=4,
            alphabet="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        )

        self.assertEqual(hashids.decode(first), (62**3,))
        self.assertEqual(hashids.decode(second), (62**3 + 1,))
        self.assertNotEqual(first, second)

    async def test_initialization_does_not_reset_a_higher_counter(self) -> None:
        redis = InMemoryRedis()
        redis.value = 500_000
        generator = RedisHashidsShortCodeGenerator(redis, "test-secret")

        await generator.initialize()

        self.assertEqual(redis.value, 500_000)
