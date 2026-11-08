from hashids import Hashids
from redis.asyncio import Redis

from src.domain.services.short_code_generator import ShortCodeGenerator


class RedisHashidsShortCodeGenerator(ShortCodeGenerator):
    _COUNTER_KEY = "url_shortner:short_code:sequence"
    _COUNTER_MINIMUM = 62**3 - 1
    _BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    def __init__(self, redis: Redis, secret_key: str) -> None:
        self._redis = redis
        self._hashids = Hashids(
            salt=secret_key,
            min_length=4,
            alphabet=self._BASE62_ALPHABET,
        )

    async def initialize(self) -> None:
        await self._redis.eval(
            """
            local current = redis.call('GET', KEYS[1])
            local minimum = tonumber(ARGV[1])
            if not current or tonumber(current) < minimum then
                redis.call('SET', KEYS[1], minimum)
                return minimum
            end
            return tonumber(current)
            """,
            1,
            self._COUNTER_KEY,
            self._COUNTER_MINIMUM,
        )

    async def generate(self) -> str:
        sequence = await self._redis.incr(self._COUNTER_KEY)
        return self._hashids.encode(sequence)
