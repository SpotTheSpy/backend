from typing import Dict

from fastapi_sa_orm_filter.operators import Operators as Ops

users_filters: Dict[str, list] = {
    "first_name": [Ops.eq, Ops.in_],
    "locale": [Ops.eq, Ops.in_],
    "created_at": [Ops.between, Ops.eq, Ops.gt, Ops.lt, Ops.in_],
}
