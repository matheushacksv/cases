from ninja import Schema
from pydantic import Field, field_validator


def clean_video_url(v: str | None) -> str | None:
    # vira href no frontend: só http(s), senão "javascript:" passaria
    if v is None:
        return v
    v = v.strip()
    if v and not v.lower().startswith(('http://', 'https://')):
        raise ValueError('link deve começar com http:// ou https://')
    return v


class CaseInDTO(Schema):
    name: str = Field(max_length=150)
    niche_raw: str = Field(max_length=150)
    result: str
    video_url: str = Field(default='', max_length=500)

    @field_validator('name', 'niche_raw', 'result')
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('campo obrigatório')
        return v

    @field_validator('video_url')
    @classmethod
    def check_video_url(cls, v: str) -> str:
        return clean_video_url(v)  # type: ignore[return-value]


class CaseOutDTO(Schema):
    id: int
    name: str
    niche_raw: str
    result: str
    video_url: str = ''
    segment_id: int | None = None
    segment_name: str | None = None

    @staticmethod
    def resolve_segment_name(obj) -> str | None:
        return obj.segment.name if obj.segment_id else None


class SegmentOutDTO(Schema):
    id: int
    name: str
    n_cases: int = 0

    @staticmethod
    def resolve_n_cases(obj):
        return getattr(obj, 'n', obj.cases.count())

class CasePatchInDTO(Schema):
    name: str | None = None
    niche: str | None = None
    result: str | None = None
    video_url: str | None = Field(default=None, max_length=500)

    @field_validator('video_url')
    @classmethod
    def check_video_url(cls, v: str | None) -> str | None:
        return clean_video_url(v)
