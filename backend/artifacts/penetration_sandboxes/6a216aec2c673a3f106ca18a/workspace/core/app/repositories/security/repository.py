from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from core.app.models.common.base import utc_now
from core.app.models.security import (
    ActionChallenge,
    DeviceFingerprint,
    DeviceIdentity,
    DeviceProofNonce,
    PasswordHistory,
    PasswordResetToken,
    RateLimitRecord,
    RegistrationOtp,
    SessionEvent,
)
from core.app.repositories.common.base import MongoRepository

MAX_LINKED_VALUES = 250
DEFAULT_PASSWORD_HISTORY_LIMIT = 10


class DeviceIdentityRepository(MongoRepository):
    collection_name = "device_identities"

    async def get_by_id(self, device_id: str) -> dict | None:
        return await self.find_one({"_id": device_id}, {"_id": 0})

    async def get_by_machine_family(self, machine_family_hash: str) -> dict | None:
        return await self.find_one(
            {"machine_family_hash": machine_family_hash},
            {"_id": 0},
        )

    async def get_by_machine_signature(self, machine_signature_hash: str) -> dict | None:
        return await self.find_one(
            {"machine_signature_hash": machine_signature_hash},
            {"_id": 0},
        )

    async def get_by_device_signature(self, device_signature_hash: str) -> dict | None:
        return await self.find_one(
            {"device_signature_hash": device_signature_hash},
            {"_id": 0},
        )

    async def list_by_ids(self, device_ids: list[str]) -> dict[str, dict]:
        scoped_ids = list(dict.fromkeys(device_id for device_id in device_ids if device_id))
        if not scoped_ids:
            return {}
        rows = await self.collection.find(
            {"_id": {"$in": scoped_ids}},
            {
                "_id": 0,
                "device_public_key": 0,
            },
        ).to_list(length=len(scoped_ids))
        return {str(row["id"]): row for row in rows if row.get("id")}

    async def has_seen_user_on_other_device(
        self,
        *,
        user_id: str,
        exclude_device_id: str,
    ) -> bool:
        return bool(
            await self.collection.find_one(
                {
                    "user_ids": user_id,
                    "_id": {"$ne": exclude_device_id},
                },
                {"_id": 1},
            )
        )

    async def get_by_public_key_for_user(
        self,
        *,
        user_id: str,
        public_key: dict[str, Any] | None,
    ) -> dict | None:
        public_key_hash = device_public_key_hash(public_key)
        if not user_id or not public_key_hash:
            return None
        return await self.find_one(
            {
                "user_ids": user_id,
                "$or": [
                    {"device_public_key_hash": public_key_hash},
                    {"device_public_key": public_key},
                ],
            },
            {"_id": 0},
        )

    async def upsert_seen(
        self,
        *,
        device_id: str,
        device_public_key: dict[str, Any],
        key_storage: str | None,
        hardware_bound: bool,
        platform_authenticator_available: bool,
        machine_family_hash: str | None,
        machine_signature_hash: str | None,
        device_signature_hash: str,
        deep_signature_hash: str | None,
        user_id: str | None,
        workspace_id: str | None,
        account_type: str | None,
        role: str | None,
        session_metadata: dict[str, Any],
        success: bool,
        confidence_score: float | None,
        risk_score: int,
        risk_reasons: list[str],
    ) -> dict:
        if machine_signature_hash is None or deep_signature_hash is None:
            return {}
        now = utc_now()
        existing = await self.get_by_id(device_id)
        public_key_hash = device_public_key_hash(device_public_key)
        if not existing:
            record = DeviceIdentity(
                id=device_id,
                device_public_key=device_public_key,
                device_public_key_hash=public_key_hash,
                key_storage=key_storage or "unknown",
                hardware_bound=hardware_bound,
                platform_authenticator_available=platform_authenticator_available,
                machine_family_hash=machine_family_hash,
                machine_signature_hash=machine_signature_hash,
                device_signature_hash=device_signature_hash,
                deep_signature_hash=deep_signature_hash,
                primary_user_id=user_id,
                primary_workspace_id=workspace_id,
                user_ids=_append_unique([], user_id),
                workspace_ids=_append_unique([], workspace_id),
                account_types=_append_unique([], account_type),
                roles=_append_unique([], role),
                first_seen_at=now,
                last_seen_at=now,
                seen_count=1,
                success_count=1 if success else 0,
                failure_count=0 if success else 1,
                confidence_score=confidence_score,
                risk_score=risk_score,
                risk_reasons=risk_reasons,
                last_ip=session_metadata.get("client_ip"),
                last_ip_hash=session_metadata.get("client_ip_hash"),
                last_user_agent_hash=session_metadata.get("user_agent_hash"),
                ip_asn=session_metadata.get("ip_asn"),
                ip_as_name=session_metadata.get("ip_as_name"),
                ip_country_code=session_metadata.get("ip_country_code"),
                ip_country=session_metadata.get("ip_country"),
            )
            return await self.insert_model(record)

        existing_public_key = existing.get("device_public_key") or {}
        existing_public_key_hash = existing.get("device_public_key_hash") or device_public_key_hash(
            existing_public_key
        )
        public_key_changed = bool(
            public_key_hash
            and existing_public_key_hash
            and public_key_hash != existing_public_key_hash
        )
        update = {
            "device_public_key": device_public_key if public_key_changed else existing_public_key or device_public_key,
            "device_public_key_hash": public_key_hash if public_key_changed else existing_public_key_hash or public_key_hash,
            "key_storage": key_storage or existing.get("key_storage") or "unknown",
            "hardware_bound": bool(hardware_bound or existing.get("hardware_bound")),
            "platform_authenticator_available": bool(
                platform_authenticator_available
                or existing.get("platform_authenticator_available")
            ),
            "key_rotation_count": int(existing.get("key_rotation_count", 0)) + (1 if public_key_changed else 0),
            "key_rotated_at": now if public_key_changed else existing.get("key_rotated_at"),
            "machine_family_hash": existing.get("machine_family_hash") or machine_family_hash,
            "machine_signature_hash": existing.get("machine_signature_hash")
            or machine_signature_hash,
            "device_signature_hash": existing.get("device_signature_hash") or device_signature_hash,
            "deep_signature_hash": deep_signature_hash,
            "primary_user_id": existing.get("primary_user_id") or user_id,
            "primary_workspace_id": existing.get("primary_workspace_id") or workspace_id,
            "user_ids": _append_unique(existing.get("user_ids", []), user_id),
            "workspace_ids": _append_unique(existing.get("workspace_ids", []), workspace_id),
            "account_types": _append_unique(existing.get("account_types", []), account_type),
            "roles": _append_unique(existing.get("roles", []), role),
            "last_seen_at": now,
            "seen_count": int(existing.get("seen_count", 0)) + 1,
            "success_count": int(existing.get("success_count", 0)) + (1 if success else 0),
            "failure_count": int(existing.get("failure_count", 0)) + (0 if success else 1),
            "confidence_score": confidence_score
            if confidence_score is not None
            else existing.get("confidence_score"),
            "risk_score": risk_score,
            "risk_reasons": risk_reasons,
            "last_ip": session_metadata.get("client_ip"),
            "last_ip_hash": session_metadata.get("client_ip_hash"),
            "last_user_agent_hash": session_metadata.get("user_agent_hash"),
            "ip_asn": session_metadata.get("ip_asn"),
            "ip_as_name": session_metadata.get("ip_as_name"),
            "ip_country_code": session_metadata.get("ip_country_code"),
            "ip_country": session_metadata.get("ip_country"),
            "updated_at": now,
        }
        await self.collection.update_one({"_id": existing["id"]}, {"$set": update})
        return await self.find_one({"_id": existing["id"]}, {"_id": 0}) or {}


class DeviceFingerprintRepository(MongoRepository):
    collection_name = "fingerprints"

    async def get_by_hash(self, fingerprint_hash: str) -> dict | None:
        return await self.find_one({"fingerprint_hash": fingerprint_hash}, {"_id": 0})

    async def latest_by_device_ids(self, device_ids: list[str]) -> dict[str, dict]:
        scoped_ids = list(dict.fromkeys(device_id for device_id in device_ids if device_id))
        if not scoped_ids:
            return {}
        rows = await (
            self.collection.find(
                {"device_id": {"$in": scoped_ids}},
                {
                    "_id": 0,
                    "fingerprint_hash": 0,
                    "machine_family_hash": 0,
                    "machine_signature_hash": 0,
                    "device_signature_hash": 0,
                    "deep_signature_hash": 0,
                },
            )
            .sort([("last_seen_at", -1), ("updated_at", -1)])
            .limit(len(scoped_ids) * 5)
            .to_list(length=len(scoped_ids) * 5)
        )
        latest: dict[str, dict] = {}
        for row in rows:
            device_id = str(row.get("device_id") or "")
            if device_id and device_id not in latest:
                latest[device_id] = row
        return latest

    async def upsert_seen(
        self,
        *,
        fingerprint_hash: str,
        device_id: str | None,
        machine_family_hash: str | None,
        machine_signature_hash: str | None,
        device_signature_hash: str | None,
        deep_signature_hash: str | None,
        user_id: str | None,
        workspace_id: str | None,
        account_type: str | None,
        role: str | None,
        session_metadata: dict[str, Any],
        device: dict[str, Any],
        success: bool,
        confidence_score: float | None,
        risk_score: int,
        risk_reasons: list[str],
    ) -> dict:
        now = utc_now()
        existing = await self.get_by_hash(fingerprint_hash)
        if not existing:
            record = DeviceFingerprint(
                fingerprint_hash=fingerprint_hash,
                device_id=device_id,
                machine_family_hash=machine_family_hash,
                machine_signature_hash=machine_signature_hash,
                device_signature_hash=device_signature_hash,
                deep_signature_hash=deep_signature_hash,
                user_ids=_append_unique([], user_id),
                workspace_ids=_append_unique([], workspace_id),
                account_types=_append_unique([], account_type),
                roles=_append_unique([], role),
                first_seen_at=now,
                last_seen_at=now,
                seen_count=1,
                success_count=1 if success else 0,
                failure_count=0 if success else 1,
                confidence_score=confidence_score,
                risk_score=risk_score,
                risk_reasons=risk_reasons,
                last_ip=session_metadata.get("client_ip"),
                last_ip_hash=session_metadata.get("client_ip_hash"),
                last_user_agent_hash=session_metadata.get("user_agent_hash"),
                ip_asn=session_metadata.get("ip_asn"),
                ip_as_name=session_metadata.get("ip_as_name"),
                ip_country_code=session_metadata.get("ip_country_code"),
                ip_country=session_metadata.get("ip_country"),
                device=device,
            )
            return await self.insert_model(record)

        update = {
            "device_id": existing.get("device_id") or device_id,
            "machine_family_hash": existing.get("machine_family_hash") or machine_family_hash,
            "machine_signature_hash": (
                existing.get("machine_signature_hash") or machine_signature_hash
            ),
            "device_signature_hash": existing.get("device_signature_hash") or device_signature_hash,
            "deep_signature_hash": deep_signature_hash or existing.get("deep_signature_hash"),
            "user_ids": _append_unique(existing.get("user_ids", []), user_id),
            "workspace_ids": _append_unique(existing.get("workspace_ids", []), workspace_id),
            "account_types": _append_unique(existing.get("account_types", []), account_type),
            "roles": _append_unique(existing.get("roles", []), role),
            "last_seen_at": now,
            "seen_count": int(existing.get("seen_count", 0)) + 1,
            "success_count": int(existing.get("success_count", 0)) + (1 if success else 0),
            "failure_count": int(existing.get("failure_count", 0)) + (0 if success else 1),
            "confidence_score": confidence_score
            if confidence_score is not None
            else existing.get("confidence_score"),
            "risk_score": risk_score,
            "risk_reasons": risk_reasons,
            "last_ip": session_metadata.get("client_ip"),
            "last_ip_hash": session_metadata.get("client_ip_hash"),
            "last_user_agent_hash": session_metadata.get("user_agent_hash"),
            "ip_asn": session_metadata.get("ip_asn"),
            "ip_as_name": session_metadata.get("ip_as_name"),
            "ip_country_code": session_metadata.get("ip_country_code"),
            "ip_country": session_metadata.get("ip_country"),
            "device": device,
            "updated_at": now,
        }
        await self.collection.update_one({"_id": existing["id"]}, {"$set": update})
        return await self.find_one({"_id": existing["id"]}, {"_id": 0}) or {}


class DeviceProofNonceRepository(MongoRepository):
    collection_name = "device_proof_nonces"

    async def consume_once(
        self,
        *,
        device_id: str,
        nonce_hash: str,
        now: datetime,
        expires_at: datetime,
    ) -> bool:
        await self.collection.delete_many({"expires_at": {"$lte": now}})
        existing = await self.find_one(
            {
                "device_id": device_id,
                "nonce_hash": nonce_hash,
                "expires_at": {"$gt": now},
            },
            {"_id": 0},
        )
        if existing:
            return False
        await self.insert_model(
            DeviceProofNonce(
                device_id=device_id,
                nonce_hash=nonce_hash,
                expires_at=expires_at,
            )
        )
        return True


class ActionChallengeRepository(MongoRepository):
    collection_name = "action_challenges"

    async def issue(
        self,
        *,
        user_id: str,
        device_id: str,
        action_scope: str,
        challenge_hash: str,
        expires_at: datetime,
    ) -> dict:
        return await self.insert_model(
            ActionChallenge(
                user_id=user_id,
                device_id=device_id,
                action_scope=action_scope,
                challenge_hash=challenge_hash,
                expires_at=expires_at,
            )
        )

    async def consume_once(
        self,
        *,
        user_id: str,
        device_id: str,
        action_scope: str,
        challenge_hash: str,
        now: datetime,
    ) -> bool:
        consumed = await self.collection.find_one_and_update(
            {
                "user_id": user_id,
                "device_id": device_id,
                "action_scope": action_scope,
                "challenge_hash": challenge_hash,
                "consumed_at": None,
                "expires_at": {"$gt": now},
            },
            {"$set": {"consumed_at": now, "updated_at": now}},
            projection={"_id": 1},
        )
        return bool(consumed)


class RegistrationOtpRepository(MongoRepository):
    collection_name = "registration_otps"

    async def create(self, challenge: RegistrationOtp) -> dict:
        return await self.insert_model(challenge)

    async def latest_active_for_email(self, email: str, *, now: datetime) -> dict | None:
        rows = await (
            self.collection.find(
                {
                    "email": email,
                    "consumed_at": None,
                    "revoked_at": None,
                    "expires_at": {"$gt": now},
                },
                {"_id": 0},
            )
            .sort([("created_at", -1)])
            .limit(1)
            .to_list(length=1)
        )
        return rows[0] if rows else None

    async def revoke_active_for_email(self, email: str, *, now: datetime) -> None:
        await self.collection.update_many(
            {
                "email": email,
                "consumed_at": None,
                "revoked_at": None,
                "expires_at": {"$gt": now},
            },
            {"$set": {"revoked_at": now, "updated_at": now}},
        )

    async def revoke(self, challenge_id: str, *, now: datetime) -> None:
        await self.collection.update_one(
            {"_id": challenge_id},
            {"$set": {"revoked_at": now, "updated_at": now}},
        )

    async def increment_attempt(self, challenge_id: str, *, now: datetime) -> dict | None:
        await self.collection.update_one(
            {"_id": challenge_id},
            {"$inc": {"attempt_count": 1}, "$set": {"updated_at": now}},
        )
        return await self.find_one({"_id": challenge_id}, {"_id": 0})

    async def consume_once(
        self,
        *,
        challenge_id: str,
        otp_hash: str,
        max_attempts: int,
        now: datetime,
    ) -> dict | None:
        result = await self.collection.update_one(
            {
                "_id": challenge_id,
                "otp_hash": otp_hash,
                "attempt_count": {"$lt": max_attempts},
                "consumed_at": None,
                "revoked_at": None,
                "expires_at": {"$gt": now},
            },
            {"$set": {"consumed_at": now, "updated_at": now}},
        )
        if not result.matched_count:
            return None
        return await self.find_one({"_id": challenge_id}, {"_id": 0})


class PasswordResetTokenRepository(MongoRepository):
    collection_name = "password_reset_tokens"

    async def create(self, token: PasswordResetToken) -> dict:
        return await self.insert_model(token)

    async def revoke_active_for_user(self, user_id: str, *, now: datetime) -> None:
        await self.collection.update_many(
            {
                "user_id": user_id,
                "used": {"$ne": True},
                "consumed_at": None,
                "revoked_at": None,
                "expires_at": {"$gt": now},
            },
            {"$set": {"revoked_at": now, "updated_at": now}},
        )

    async def get_active_by_hash(self, token_hash: str, *, now: datetime) -> dict | None:
        return await self.find_one(
            {
                "token_hash": token_hash,
                "used": {"$ne": True},
                "consumed_at": None,
                "revoked_at": None,
                "expires_at": {"$gt": now},
            },
            {"_id": 0},
        )

    async def get_by_hash(self, token_hash: str) -> dict | None:
        return await self.find_one({"token_hash": token_hash}, {"_id": 0})

    async def consume_once(self, *, token_hash: str, now: datetime) -> dict | None:
        return await self.collection.find_one_and_update(
            {
                "token_hash": token_hash,
                "used": {"$ne": True},
                "consumed_at": None,
                "revoked_at": None,
                "expires_at": {"$gt": now},
            },
            {"$set": {"used": True, "consumed_at": now, "updated_at": now}},
            projection={"_id": 0},
        )


class PasswordHistoryRepository(MongoRepository):
    collection_name = "password_history"

    async def create(self, item: PasswordHistory) -> dict:
        return await self.insert_model(item)

    async def list_for_user(
        self,
        user_id: str,
        *,
        limit: int = DEFAULT_PASSWORD_HISTORY_LIMIT,
    ) -> list[dict]:
        capped_limit = max(1, limit)
        return await (
            self.collection.find(
                {"user_id": user_id},
                {"_id": 0},
            )
            .sort("created_at", -1)
            .limit(capped_limit)
            .to_list(length=capped_limit)
        )

    async def prune_for_user(
        self,
        user_id: str,
        *,
        keep: int = DEFAULT_PASSWORD_HISTORY_LIMIT,
    ) -> int:
        capped_keep = max(1, keep)
        stale_rows = await (
            self.collection.find(
                {"user_id": user_id},
                {"_id": 1, "created_at": 1},
            )
            .sort("created_at", -1)
            .skip(capped_keep)
            .to_list(length=500)
        )
        stale_ids = [row["_id"] for row in stale_rows if row.get("_id")]
        if not stale_ids:
            return 0
        result = await self.collection.delete_many({"_id": {"$in": stale_ids}})
        return int(result.deleted_count)


class RateLimitRepository(MongoRepository):
    collection_name = "rate_limits"

    async def get_active(
        self,
        *,
        scope: str,
        identifier_type: str,
        identifier_hash: str,
        now: datetime,
    ) -> dict | None:
        return await self.find_one(
            {
                "scope": scope,
                "identifier_type": identifier_type,
                "identifier_hash": identifier_hash,
                "expires_at": {"$gt": now},
            },
            {"_id": 0},
        )

    async def save_attempt(
        self,
        *,
        scope: str,
        identifier_type: str,
        identifier_hash: str,
        reason: str,
        metadata: dict[str, Any],
        now: datetime,
        expires_at: datetime,
        blocked_until: datetime | None,
    ) -> dict:
        existing = await self.get_active(
            scope=scope,
            identifier_type=identifier_type,
            identifier_hash=identifier_hash,
            now=now,
        )
        if not existing:
            record = RateLimitRecord(
                scope=scope,
                identifier_type=identifier_type,
                identifier_hash=identifier_hash,
                attempt_count=1,
                violation_count=1 if blocked_until else 0,
                blocked_until=blocked_until,
                expires_at=expires_at,
                first_attempt_at=now,
                last_attempt_at=now,
                last_reason=reason,
                metadata=metadata,
            )
            return await self.insert_model(record)

        update = {
            "attempt_count": int(existing.get("attempt_count", 0)) + 1,
            "violation_count": int(existing.get("violation_count", 0))
            + (1 if blocked_until else 0),
            "blocked_until": blocked_until or existing.get("blocked_until"),
            "expires_at": expires_at,
            "last_attempt_at": now,
            "last_reason": reason,
            "metadata": metadata,
            "updated_at": now,
        }
        await self.collection.update_one({"_id": existing["id"]}, {"$set": update})
        return await self.find_one({"_id": existing["id"]}, {"_id": 0}) or {}

    async def clear_active(
        self,
        *,
        scope: str,
        identifier_type: str,
        identifier_hash: str,
        now: datetime,
    ) -> None:
        record = await self.get_active(
            scope=scope,
            identifier_type=identifier_type,
            identifier_hash=identifier_hash,
            now=now,
        )
        if not record:
            return
        await self.collection.update_one(
            {"_id": record["id"]},
            {
                "$set": {
                    "attempt_count": 0,
                    "blocked_until": None,
                    "expires_at": now,
                    "updated_at": now,
                }
            },
        )


class SessionEventRepository(MongoRepository):
    collection_name = "session_events"

    async def create(self, event: SessionEvent) -> dict:
        return await self.insert_model(event)

    async def latest_login_by_user_ids(
        self,
        *,
        user_ids: list[str],
        workspace_id: str,
    ) -> dict[str, datetime]:
        if not user_ids:
            return {}
        events = await self.collection.find(
            {
                "user_id": {"$in": user_ids},
                "workspace_id": workspace_id,
                "event_type": "login",
            },
            {"_id": 0, "user_id": 1, "event_at": 1},
        ).sort([("event_at", -1)]).limit(1000).to_list(length=1000)
        latest: dict[str, datetime] = {}
        for event in events:
            user_id = event.get("user_id")
            event_at = event.get("event_at")
            if user_id and isinstance(event_at, datetime) and user_id not in latest:
                latest[user_id] = event_at
        return latest


def _append_unique(values: list[str], value: str | None, *, limit: int = 100) -> list[str]:
    if not value or value in values:
        return values
    return [*values, value][:limit]


def device_public_key_hash(public_key: dict[str, Any] | None) -> str | None:
    if not public_key:
        return None
    encoded = json.dumps(public_key, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
