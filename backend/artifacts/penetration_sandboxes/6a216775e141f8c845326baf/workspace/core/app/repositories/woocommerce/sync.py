from __future__ import annotations

from datetime import datetime
from typing import Any

from core.app.models.common.base import utc_now
from core.app.repositories.common.base import MongoRepository


class WooSyncStatusRepository(MongoRepository):
    collection_name = "woo_sync_status"
    _tenant_scoped = True

    async def get_by_workspace(self, workspace_id: str) -> dict | None:
        return await self.find_one(
            {"workspace_id": workspace_id, "provider": "woocommerce"},
            {"_id": 0},
        )

    async def list_webhook_repair_candidates(
        self,
        *,
        stale_before: datetime,
        limit: int,
    ) -> list[dict]:
        safe_limit = max(1, min(limit, 500))
        filter_query = {
            "provider": "woocommerce",
            "connection_status": "connected",
            "credentials_valid": {"$ne": False},
            "$or": [
                {"webhook_last_delivery_at": {"$lte": stale_before}},
                {
                    "webhook_last_delivery_at": None,
                    "webhook_health": {"$ne": "healthy"},
                },
                {
                    "webhook_last_delivery_at": {"$exists": False},
                    "webhook_health": {"$ne": "healthy"},
                },
            ],
        }
        cursor = (
            self.collection.find(filter_query, {"_id": 0})
            .sort("updated_at", 1)
            .limit(safe_limit)
        )
        return await cursor.to_list(length=safe_limit)

    async def upsert_status(self, workspace_id: str, fields: dict[str, Any]) -> dict:
        from core.app.models.common.base import new_id
        document = dict(fields)
        document.update({
            "workspace_id": workspace_id,
            "provider": "woocommerce",
            "updated_at": utc_now(),
        })
        # Ensure id exists for new documents (matches MongoModel behavior)
        if "id" not in document:
            document["id"] = new_id("woosync")
        # Remove created_at from $set to avoid conflict with $setOnInsert
        document.pop("created_at", None)
        await self.collection.update_one(
            {"workspace_id": workspace_id, "provider": "woocommerce"},
            {
                "$set": document,
                "$setOnInsert": {"created_at": utc_now()},
            },
            upsert=True,
        )
        return await self.get_by_workspace(workspace_id) or {}

    async def try_start_sync(self, workspace_id: str) -> bool:
        now = utc_now()
        result = await self.collection.update_one(
            {
                "workspace_id": workspace_id,
                "provider": "woocommerce",
                "sync_in_progress": {"$ne": True},
            },
            {
                "$set": {
                    "sync_in_progress": True,
                    "sync_state": "queued",
                    "sync_progress_percent": 0,
                    "sync_started_at": now,
                    "last_sync_error": None,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "workspace_id": workspace_id,
                    "provider": "woocommerce",
                    "created_at": now,
                },
            },
            upsert=True,
        )
        return bool(result.modified_count or result.upserted_id)

    async def force_finish_sync(self, workspace_id: str) -> None:
        await self.collection.update_one(
            {"workspace_id": workspace_id, "provider": "woocommerce"},
            {
                "$set": {
                    "sync_in_progress": False,
                    "sync_state": "failed",
                    "updated_at": utc_now(),
                },
            },
            upsert=True,
        )

    async def increment_webhook_stats(
        self, workspace_id: str, *, delivered: bool = False, failed: bool = False
    ) -> None:
        set_fields: dict[str, Any] = {"updated_at": utc_now()}
        inc_fields: dict[str, Any] = {}
        if delivered:
            inc_fields["webhook_delivery_count_24h"] = 1
            set_fields["webhook_last_delivery_at"] = utc_now()
        if failed:
            inc_fields["webhook_failure_count_24h"] = 1
        if delivered or failed:
            set_fields["webhook_last_delivery_at"] = utc_now()
        update: dict[str, Any] = {"$set": set_fields}
        if inc_fields:
            update["$inc"] = inc_fields
        await self.collection.update_one(
            {"workspace_id": workspace_id, "provider": "woocommerce"},
            update,
            upsert=True,
        )
