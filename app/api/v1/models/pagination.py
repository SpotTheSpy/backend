from typing import Generic, TypeVar, Annotated, Type, Sequence

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Executable

from app.database.models import Base

T = TypeVar("T", bound=BaseModel)
Q = TypeVar("Q", bound=Executable)


class PaginationMeta(BaseModel):
    """
    Result pagination parameters.

    Attributes:
        limit: Results count limit in an output.
        offset: Search offset.
    """

    limit: int
    """
    Results count limit in an output.
    """

    offset: int
    """
    Search offset.
    """


class PaginatedResult(BaseModel, Generic[T]):
    """
    Results list of selected model instances along with pagination parameters.

    Attributes:
        results: List of model instances.
        meta: Pagination parameters.
    """

    results: list[T]
    """
    List of model instances.
    """

    meta: PaginationMeta
    """
    Pagination parameters.
    """


class PaginationParams(BaseModel):
    """
    Pagination parameters model.

    Attributes:
        limit: Results count limit in an output.
        offset: Search offset.
    """

    limit: Annotated[int, Query(ge=0, le=100)] = 100
    """
    Results count limit in an output.
    """

    offset: Annotated[int, Query(ge=0)] = 0
    """
    Search offset.
    """

    def apply(
            self,
            query: Q
    ) -> Q:
        """
        Apply pagination parameters to an SQL query.
        :param query: SQL query.
        :return: Query with pagination parameters.
        """

        return query.limit(self.limit).offset(self.offset)

    def create_response(
            self,
            results: Sequence[BaseModel | Base],
            model: Type[T]
    ) -> PaginatedResult[T]:
        """
        Create response model from a paginated query output.

        :param results: Sequence of object instances.
        :param model: Pagination model type.
        :return: Response model with list of model instances and pagination parameters.
        """
        return PaginatedResult[model](
            results=results,
            meta=PaginationMeta(
                limit=self.limit,
                offset=self.offset
            )
        )
