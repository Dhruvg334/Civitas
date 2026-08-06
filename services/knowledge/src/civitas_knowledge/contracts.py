from pydantic import BaseModel, Field


class PolicyReference(BaseModel):
    policy_id: str
    title: str
    excerpt: str
    source: str
    tags: list[str] = Field(default_factory=list)
