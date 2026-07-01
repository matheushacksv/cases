from typing import List

from ninja import Router, Status
from ninja.pagination import PageNumberPagination, paginate

from api.security import api_key_auth
from apps.cases import services
from apps.cases.schemas import CaseInDTO, CaseOutDTO, CasePatchInDTO, SegmentOutDTO

router = Router(tags=['Cases'])


@router.post('/cases', response={201: CaseOutDTO}, auth=api_key_auth)
def create_case_endpoint(request, payload: CaseInDTO):
    return Status(201, services.create_case(payload))


@router.get('/segments', response={200: List[SegmentOutDTO]})
def list_segment_endpoint(request):
    return Status(200, services.list_segments())


@router.get('/cases', response={200: List[CaseOutDTO]})
@paginate(PageNumberPagination, page_size=12)
def list_cases_endpoint(
    request, segment_id: int | None = None, query: str | None = None
):
    return services.list_cases(segment_id, query)


@router.get('/search', response={200: List[CaseOutDTO]})
def search_cases_endpoint(request, query: str, limit: int = 10):
    return Status(200, services.search_case(query, limit))


@router.patch('/cases/{case_id}', response={200: CaseOutDTO}, auth=api_key_auth)
def update_case_endpoint(request, case_id: int, payload: CasePatchInDTO):
    return Status(
        200, services.update_case(case_id, payload.name, payload.niche, payload.result)
    )
