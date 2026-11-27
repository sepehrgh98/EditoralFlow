"""Request bodies shared by the routes."""

from pydantic import BaseModel, Field, field_validator


class ArticleRequest(BaseModel):
    article: str = Field(min_length=1, description="The article text.")

    @field_validator("article")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("article must not be blank")
        return value
