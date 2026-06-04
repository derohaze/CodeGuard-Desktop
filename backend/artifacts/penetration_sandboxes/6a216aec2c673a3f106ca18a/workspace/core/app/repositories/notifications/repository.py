from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo import DESCENDING

from core.app.models.notifications.entity import Notification
from core.app.repositories.common.base import MongoRepository, clean_mongo_document


class NotificationRepository(MongoRepository):
    collection_name = "notifications"
    _tenant_scoped = True

    async def create(self, notification: Notification) -> dict[str, Any]:
        return await self.insert_model(notification)

    @staticmethod
    def _audience_query(*, user_id: str, role: str, store_id: str | None) -> dict[str, Any]:
        query: dict[str, Any] = {
            "$and": [
                {
                    "$or": [
                        {"audience_roles": role},
                        {"audience_user_ids": user_id},
                    ]
                }
            ]
        }
        if role != "owner":
            store_scope = [{"store_id": None}]
            if store_id:
                store_scope.append({"store_id": store_id})
            query["$and"].append({"$or": store_scope})
        return query

    async def get_for_resource(
        self,
        *,
        workspace_id: str,
        resource_type: str,
        resource_id: str,
    ) -> dict[str, Any] | None:
        return await self.find_one(
            {
                "workspace_id": workspace_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "deleted_at": None,
            },
            {"_id": 0},
        )

    async def list_for_audience(
        self,
        *,
        workspace_id: str,
        user_id: str,
        role: str,
        store_id: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {
            "workspace_id": workspace_id,
            "deleted_at": None,
            **self._audience_query(user_id=user_id, role=role, store_id=store_id),
        }
        rows = await (
            self.collection.find(query, {"_id": 0})
            .sort([("created_at", DESCENDING), ("id", DESCENDING)])
            .limit(limit * 2)
            .to_list(length=limit * 2)
        )
        return [
            clean_mongo_document(row) or {}
            for row in rows
            if user_id not in (row.get("deleted_by_user_ids") or [])
        ][:limit]

    async def mark_read_for_user(
        self,
        *,
        workspace_id: str,
        notification_id: str,
        user_id: str,
        role: str,
        store_id: str | None,
        updated_at: datetime,
    ) -> dict[str, Any] | None:
        query: dict[str, Any] = {
            "_id": notification_id,
            "workspace_id": workspace_id,
            "deleted_at": None,
            **self._audience_query(user_id=user_id, role=role, store_id=store_id),
        }
        result = await self.collection.find_one_and_update(
            query,
            {
                "$addToSet": {"read_by_user_ids": user_id},
                "$set": {"updated_at": updated_at},
            },
            projection={"_id": 0},
            return_document=True,
        )
        return clean_mongo_document(result)

    async def mark_all_read_for_user(
        self,
        *,
        workspace_id: str,
        user_id: str,
        role: str,
        store_id: str | None,
        updated_at: datetime,
    ) -> int:
        query: dict[str, Any] = {
            "workspace_id": workspace_id,
            "deleted_at": None,
            **self._audience_query(user_id=user_id, role=role, store_id=store_id),
        }
        result = await self.collection.update_many(
            query,
            {
                "$addToSet": {"read_by_user_ids": user_id},
                "$set": {"updated_at": updated_at},
            },
        )
        return int(getattr(result, "modified_count", 0) or 0)

    async def hide_all_for_user(
        self,
        *,
        workspace_id: str,
        user_id: str,
        role: str,
        store_id: str | None,
        updated_at: datetime,
    ) -> int:
        query: dict[str, Any] = {
            "workspace_id": workspace_id,
            "deleted_at": None,
            **self._audience_query(user_id=user_id, role=role, store_id=store_id),
        }
        result = await self.collection.update_many(
            query,
            {
                "$addToSet": {"deleted_by_user_ids": user_id},
                "$set": {"updated_at": updated_at},
            },
        )
        return int(getattr(result, "modified_count", 0) or 0)
