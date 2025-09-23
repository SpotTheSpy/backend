from typing import Generic, TypeVar, Annotated, Type, Sequence

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Executable

from app.database.models import Base

T = TypeVar("T", bound=BaseModel)
Q = TypeVar("Q", bound=Executable)


class PaginationMeta(BaseModel):
    limit: int
    offset: int


class PaginatedResult(BaseModel, Generic[T]):
    results: list[T]
    meta: PaginationMeta


class PaginationParams(BaseModel):
    limit: Annotated[int, Query(ge=0, le=100)] = 100
    offset: Annotated[int, Query(ge=0)] = 0

    def apply(
            self,
            query: Q
    ) -> Q:
        return query.limit(self.limit).offset(self.offset)

    def create_response(
            self,
            results: Sequence[BaseModel | Base],
            model: Type[T]
    ) -> PaginatedResult[T]:
        return PaginatedResult[model](
            results=results,
            meta=PaginationMeta(
                limit=self.limit,
                offset=self.offset
            )
        )
