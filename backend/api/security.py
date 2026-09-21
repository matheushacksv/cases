import secrets

from decouple import config
from ninja.security import APIKeyHeader


class ApiKeyAuth(APIKeyHeader):
    param_name = 'X-API-Key'

    def authenticate(self, request, key):
        # ADMIN_PASSWORD é a senha do login do site; API_KEY segue valendo p/ scripts.
        # bytes: compare_digest levanta TypeError em str não-ASCII (ex.: senha com "ç").
        valid = [str(config('API_KEY')), str(config('ADMIN_PASSWORD', default=''))]
        if key and any(
            v and secrets.compare_digest(key.encode(), v.encode()) for v in valid
        ):
            return key
        return None


api_key_auth = ApiKeyAuth()
