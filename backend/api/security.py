import secrets

from decouple import config
from ninja.security import APIKeyHeader


class ApiKeyAuth(APIKeyHeader):
    param_name = 'X-API-Key'

    def authenticate(self, request, key):
        expected = str(config('API_KEY'))
        if key and secrets.compare_digest(key, expected):
            return key
        return None


api_key_auth = ApiKeyAuth()
