import os
from unittest import mock

from django.test import SimpleTestCase

from api.security import api_key_auth

ENV = {'API_KEY': 'chave-api', 'ADMIN_PASSWORD': 'sénha-admin'}


class ApiKeyAuthTests(SimpleTestCase):
    def check(self, key):
        with mock.patch.dict(os.environ, ENV):
            return api_key_auth.authenticate(None, key)

    def test_aceita_admin_password_mesmo_nao_ascii(self):
        self.assertTrue(self.check('sénha-admin'))

    def test_aceita_api_key(self):
        self.assertTrue(self.check('chave-api'))

    def test_recusa_errada_e_vazia(self):
        self.assertFalse(self.check('outra'))
        self.assertFalse(self.check(''))

    def test_admin_password_ausente_nao_libera_vazio(self):
        with mock.patch.dict(os.environ, {'API_KEY': 'x'}, clear=False):
            os.environ.pop('ADMIN_PASSWORD', None)
            self.assertFalse(api_key_auth.authenticate(None, ''))
