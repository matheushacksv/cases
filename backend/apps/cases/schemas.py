from ninja import Schema
from pydantic import Field, field_validator


class CaseInDTO(Schema):
    name: str = Field(max_length=150)
    niche_raw: str = Field(max_length=150)
    result: str

    @field_validator('name', 'niche_raw', 'result')
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('campo obrigatório')
        return v


class CaseOutDTO(Schema):
    id: int
    name: str
    niche_raw: str
    result: str
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
