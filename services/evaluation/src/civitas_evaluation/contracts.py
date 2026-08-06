from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    case_id: str
    input_payload: dict[str, object]
    expected_output: dict[str, object]
    tags: list[str] = Field(default_factory=list)
