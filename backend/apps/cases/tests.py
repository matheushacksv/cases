from unittest import mock

from django.test import TestCase

from apps.accounts.models import User

from . import services
from .schemas import CaseInDTO


class CaseAdminChangeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(email='admin@admin.com', password='x')
        self.client.force_login(self.user)

    def test_change_view_nao_quebra_com_niche_vec_populado(self):
        # niche_vec é numpy.ndarray (pgvector); readonly_fields nele quebrava
        # o admin (ValueError: truth value of array ambiguous). Regressão.
        with mock.patch('apps.cases.services.embed', return_value=[0.1] * 1536):
            case = services.create_case(
                CaseInDTO(name='Loja X', niche_raw='roupas', result='ok')
            )
        resp = self.client.get(f'/admin/cases/case/{case.id}/change/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="segment"')
