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

    def test_save_sem_mudar_niche_raw_nao_quebra(self):
        # "not obj.niche_vec" (numpy.ndarray) levantava o mesmo ValueError
        # na hora de salvar sem tocar no nicho — ex.: só trocar o segmento.
        with mock.patch('apps.cases.services.embed', return_value=[0.1] * 1536):
            case = services.create_case(
                CaseInDTO(name='Loja X', niche_raw='roupas', result='ok')
            )
        from .models import Segment

        seg2 = Segment.objects.create(name='outro segmento', centroid=[0.2] * 1536)
        resp = self.client.post(
            f'/admin/cases/case/{case.id}/change/',
            {
                'name': case.name,
                'niche_raw': case.niche_raw,
                'result': case.result,
                'video_url': '',
                'segment': seg2.id,
            },
        )
        self.assertEqual(resp.status_code, 302)
        case.refresh_from_db()
        self.assertEqual(case.segment_id, seg2.id)


class SegmentAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(email='admin@admin.com', password='x')
        self.client.force_login(self.user)

    def test_add_sem_centroid_gera_via_embed(self):
        from .models import Segment

        with mock.patch('apps.cases.admin.embed', return_value=[0.3] * 1536):
            resp = self.client.post(
                '/admin/cases/segment/add/', {'name': 'nicho novo'}
            )
        self.assertEqual(resp.status_code, 302)
        seg = Segment.objects.get(name='nicho novo')
        self.assertEqual(len(seg.centroid), 1536)

    def test_save_sem_mudar_name_nao_quebra(self):
        # "not obj.centroid" (numpy.ndarray) tinha o mesmo bug do CaseAdmin.
        from .models import Segment

        seg = Segment.objects.create(name='nicho existente', centroid=[0.4] * 1536)
        resp = self.client.post(
            f'/admin/cases/segment/{seg.id}/change/', {'name': seg.name}
        )
        self.assertEqual(resp.status_code, 302)
