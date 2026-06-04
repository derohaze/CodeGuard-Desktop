from __future__ import annotations

from datetime import UTC, datetime, timedelta

from core.app.models.common.base import utc_now
from core.app.models.webhooks.entity import WebhookIntegration
from core.app.models.webhooks.event import WebhookEvent
from core.app.repositories.common.base import MongoRepository, normalize_page, paginated_payload


class WebhookIntegrationRepository(MongoRepository):
    collection_name = "webhook_integrations"
    _tenant_scoped = True

    async def get_active(self, workspace_id: str, provider: str) -> dict | None:
        return await self.find_one(
            {"workspace_id": workspace_id, "provider": provider, "active": True},
            {"_id": 0},
        )

    async def find_by_workspace_and_token(
        self, workspace_id: str, provider: str, token_hash: str
    ) -> dict | None:
        return await self.find_one(
            {
                "workspace_id": workspace_id,
                "provider": provider,
                "token_hash": token_hash,
                "active": True,
            },
            {"_id": 0},
        )

    async def deactivate_active(self, workspace_id: str, provider: str) -> None:
        await self.collection.update_many(
            {"workspace_id": workspace_id, "provider": provider, "active": True},
            {"$set": {"active": False, "updated_at": utc_now()}},
        )

    async def delete_active(self, workspace_id: str, provider: str) -> bool:
        result = await self.collection.delete_many(
            {"workspace_id": workspace_id, "provider": provider, "active": True}
        )
        return result.deleted_count > 0

    async def insert(self, integration: WebhookIntegration) -> dict:
        return await self.insert_model(integration)


class WebhookEventRepository(MongoRepository):
    collection_name = "webhook_events"
    _tenant_scoped = True
    _node_queue_replay_grace = timedelta(minutes=10)

    async def insert(self, event: WebhookEvent) -> dict:
        return await self.insert_model(event)

    async def find_by_provider_event_id(
        self,
        *,
        workspace_id: str,
        provider: str,
        event_id: str,
    ) -> dict | None:
        return await self.find_one(
            {
                "workspace_id": workspace_id,
                "provider": provider,
                "event_id": event_id,
            },
            {"_id": 0},
        )

    async def find_by_content_hash(
        self,
        *,
        workspace_id: str,
        provider: str,
        content_hash: str,
        since: datetime | None = None,
    ) -> dict | None:
        query: dict[str, object] = {
            "workspace_id": workspace_id,
            "provider": provider,
            "content_hash": content_hash,
        }
        if since is not None:
            query["received_at"] = {"$gte": since}
        return await self.find_one(query, {"_id": 0})

    async def mark_processed(self, event_id: str) -> None:
        await self.collection.update_one(
            {"_id": event_id},
            {
                "$set": {"processed_at": utc_now()},
                "$unset": {
                    "processing_error": "",
                    "failed_at": "",
                    "queued_to_node_at": "",
                    "node_queue": "",
                },
            },
        )

    async def mark_queued_to_node(self, event_id: str, *, queue_name: str) -> None:
        await self.collection.update_one(
            {"_id": event_id},
            {
                "$set": {
                    "queued_to_node_at": utc_now(),
                    "node_queue": queue_name[:120],
                },
                "$unset": {
                    "processed_at": "",
                    "processing_error": "",
                    "failed_at": "",
                },
            },
        )

    async def mark_failed(self, event_id: str, error: str) -> None:
        await self.collection.update_one(
            {"_id": event_id},
            {
                "$set": {"processing_error": error[:1000], "failed_at": utc_now()},
                "$unset": {
                    "processed_at": "",
                    "queued_to_node_at": "",
                    "node_queue": "",
                },
            },
        )

    async def get_event(self, event_id: str) -> dict | None:
        return await self.find_one({"_id": event_id}, {"_id": 0})

    async def list_recent_unprocessed(self, *, provider: str, limit: int) -> list[dict]:
        safe_limit = max(1, limit)
        stale_node_queue_before = utc_now() - self._node_queue_replay_grace
        cursor = (
            self.collection.find(
                {
                    "provider": provider,
                    "$or": [
                        {"processing_error": {"$nin": [None, ""]}},
                        {
                            "processed_at": None,
                            "$or": [
                                {"queued_to_node_at": {"$exists": False}},
                                {"queued_to_node_at": None},
                                {"queued_to_node_at": {"$lte": stale_node_queue_before}},
                            ],
                        },
                    ],
                },
            )
            .sort("received_at", -1)
            .limit(safe_limit)
        )
        return await cursor.to_list(length=safe_limit)

    async def list_recent_for_workspace(
        self,
        *,
        workspace_id: str,
        provider: str,
        page: int,
        page_size: int,
        hours: int = 48,
    ) -> dict:
        safe_hours = max(1, min(hours, 168))
        page, page_size, skip = normalize_page(page, page_size)
        since = datetime.now(UTC) - timedelta(hours=safe_hours)
        filter_query = {
            "workspace_id": workspace_id,
            "provider": provider,
            "received_at": {"$gte": since},
        }
        total = await self.collection.count_documents(filter_query)
        rows = await (
            self.collection.find(filter_query, {"_id": 0, "payload": 0})
            .sort("received_at", -1)
            .skip(skip)
            .limit(page_size)
            .to_list(length=page_size)
        )
        return paginated_payload(rows, page, page_size, total)
