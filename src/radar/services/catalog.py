from typing import Literal
from pydantic import BaseModel, Field


class CatalogQuery(BaseModel):
    kind: Literal['article','repo'] | None = None
    q: str = Field(default='', max_length=200)
    bookmarked: bool = False
    sort: Literal['recent','stars'] = 'recent'
    limit: int = Field(default=40, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    stage: Literal['discovered','docs_checked','local_passed','adopted'] | None = None


class Catalog:
    def __init__(self, store):
        self.store = store

    def search(self, query: CatalogQuery):
        return {'items': self.store.items(**query.model_dump())}

    def get(self, item_id):
        rows = self.store.items(item_id=item_id, limit=1)
        if not rows:
            raise ValueError('NOT_FOUND: item does not exist; search for a valid item ID')
        return {'item': rows[0]}

    def history(self, item_id):
        try:
            return {'history': self.store.verifications(item_id)}
        except KeyError:
            raise ValueError('NOT_FOUND: item does not exist') from None
