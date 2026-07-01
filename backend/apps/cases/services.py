from django.db.models import Count, Q
from ninja.errors import HttpError
from openai import OpenAIError
from pgvector.django import CosineDistance

from .embeddings import embed
from .models import Case, Segment

THRESHOLD = 0.45
SEARCH_MAX_DIST = 0.5


def assign_segment(niche_raw: str) -> tuple[Segment, list[float]]:
    vect = embed(niche_raw)

    nearest = (
        Segment.objects.annotate(dist=CosineDistance('centroid', vect))
        .order_by('dist')
        .first()
    )

    if nearest and nearest.dist <= THRESHOLD:  # type: ignore
        return nearest, vect

    seg = Segment.objects.create(name=niche_raw, centroid=vect)
    return seg, vect


def create_case(data):
    try:
        segment, vec = assign_segment(data.niche_raw.strip())
    except OpenAIError:
        raise HttpError(503, 'classificação indisponivel')

    return Case.objects.create(
        name=data.name.strip(),
        niche_raw=data.niche_raw.strip(),
        niche_vec=vec,
        segment=segment,
        result=data.result,
    )


def update_case(
    case_id: int,
    name: str | None = None,
    niche: str | None = None,
    result: str | None = None,
):
    case = Case.objects.filter(id=case_id).first()

    if case is None:
        raise HttpError(404, 'not found')

    if name:
        case.name = name.strip()
    if niche:
        try:
            case.niche_vec = embed(niche.strip())
        except OpenAIError:
            raise HttpError(503, 'classificação indisponivel')
        case.niche_raw = niche.strip()
    if result:
        case.result = result

    case.save()
    return case


def list_segments():
    return Segment.objects.annotate(n=Count('cases')).order_by('-n')


def list_cases(segment_id: int | None = None, query: str | None = None):
    qs = Case.objects.select_related('segment')

    if segment_id:
        qs = qs.filter(segment_id=segment_id)
    if query:
        qs = qs.filter(niche_raw__icontains=query)
    return qs.order_by('-created_at')


def search_case(query: str, limit: int = 10):
    vec = embed(query)
    kw = (
        Q(name__unaccent__icontains=query)
        | Q(niche_raw__unaccent__icontains=query)
        | Q(result__unaccent__icontains=query)
    )

    return (
        Case.objects.select_related('segment')
        .annotate(d=CosineDistance('niche_vec', vec), is_kw=kw)
        .filter(kw | Q(d__lte=SEARCH_MAX_DIST))
        .order_by('-is_kw', 'd')[:limit]
    )
