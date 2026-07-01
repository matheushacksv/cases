from functools import lru_cache

from decouple import config
from openai import OpenAI

_MODEL = 'text-embedding-3-small'


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    return OpenAI(api_key=str(config('OPENAI_API_KEY')))


@lru_cache(maxsize=4096)
def embed(text: str) -> list[float]:
    resp = _client().embeddings.create(model=_MODEL, input=text)
    return resp.data[0].embedding
