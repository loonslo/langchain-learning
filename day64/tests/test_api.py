from fastapi.testclient import TestClient

from customer_support.api import create_app
from customer_support.sync import SyncPlan


class Product:
    def plan_sync(self, previous):
        assert previous == {"old.md": "hash"}
        return SyncPlan(("new.md",), ("old.md",))


def test_incremental_sync_plan_is_reachable_from_the_product_api():
    response = TestClient(create_app(Product())).post(
        "/knowledge/sync-plan", json={"previous": {"old.md": "hash"}}
    )
    assert response.json() == {"upsert": ["new.md"], "delete": ["old.md"]}
