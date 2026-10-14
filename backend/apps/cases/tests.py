import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

from django.test import TestCase

from apps.accounts.models import User

from . import services
from .schemas import CaseInDTO
from .video import extract_drive_id, fetch_as_mp4

SAMPLE_MOV = Path(__file__).parent / 'testdata' / 'sample.mov'


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


class ExtractDriveIdTests(TestCase):
    def test_formatos_comuns_de_link(self):
        cases = {
            'https://drive.google.com/file/d/ABC123/view?usp=sharing': 'ABC123',
            'https://drive.google.com/open?id=XYZ789': 'XYZ789',
            'https://drive.google.com/uc?id=QWE456&export=download': 'QWE456',
        }
        for url, expected in cases.items():
            self.assertEqual(extract_drive_id(url), expected)

    def test_link_nao_drive_retorna_none(self):
        self.assertIsNone(extract_drive_id('https://example.com/video.mp4'))


def _fake_gdown_download(id, output, quiet=True):
    shutil.copyfile(SAMPLE_MOV, output)


class FetchAsMp4Tests(TestCase):
    def test_remux_mov_real_gera_mp4_valido(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch('apps.cases.video.gdown.download', side_effect=_fake_gdown_download):
                out = fetch_as_mp4(
                    'https://drive.google.com/file/d/ABC123/view', Path(tmp)
                )
            self.assertTrue(out.exists())
            probe = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=format_name', str(out)],
                capture_output=True, text=True,
            )
            self.assertIn('mp4', probe.stdout)

    def test_link_nao_drive_da_422(self):
        from ninja.errors import HttpError

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(HttpError) as ctx:
                fetch_as_mp4('https://example.com/video.mp4', Path(tmp))
            self.assertEqual(ctx.exception.status_code, 422)


class DownloadCaseVideoEndpointTests(TestCase):
    def test_endpoint_devolve_mp4_com_content_disposition(self):
        with mock.patch('apps.cases.services.embed', return_value=[0.1] * 1536):
            case = services.create_case(
                CaseInDTO(
                    name='Loja X', niche_raw='roupas', result='ok',
                    video_url='https://drive.google.com/file/d/ABC123/view',
                )
            )
        with mock.patch('apps.cases.video.gdown.download', side_effect=_fake_gdown_download):
            resp = self.client.get(f'/api/cases/{case.id}/video.mp4')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'video/mp4')
        self.assertIn('attachment', resp['Content-Disposition'])
        self.assertIn('.mp4', resp['Content-Disposition'])

    def test_case_sem_video_da_404(self):
        with mock.patch('apps.cases.services.embed', return_value=[0.1] * 1536):
            case = services.create_case(
                CaseInDTO(name='Loja Y', niche_raw='roupas', result='ok')
            )
        resp = self.client.get(f'/api/cases/{case.id}/video.mp4')
        self.assertEqual(resp.status_code, 404)

    def test_case_inexistente_da_404(self):
        resp = self.client.get('/api/cases/999999/video.mp4')
        self.assertEqual(resp.status_code, 404)


class ListCasesHasVideoTests(TestCase):
    def test_filtra_so_com_video(self):
        with mock.patch('apps.cases.services.embed', return_value=[0.1] * 1536):
            services.create_case(
                CaseInDTO(
                    name='A', niche_raw='x', result='ok',
                    video_url='https://drive.google.com/file/d/ABC/view',
                )
            )
            services.create_case(CaseInDTO(name='B', niche_raw='y', result='ok'))

        self.assertEqual(services.list_cases().count(), 2)
        self.assertEqual(services.list_cases(has_video=True).count(), 1)
        self.assertEqual(services.list_cases(has_video=False).count(), 2)
