from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class InsertOneResult:
    inserted_id: str


@dataclass
class UpdateResult:
    matched_count: int
    modified_count: int
    upserted_id: str | None = None


@dataclass
class DeleteResult:
    deleted_count: int


class InMemoryCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents
        self._skip = 0
        self._limit: int | None = None

    def sort(self, sort_spec: list[tuple[str, int]] | tuple[str, int] | str, direction: int = 1):
        specs: list[tuple[str, int]]
        if isinstance(sort_spec, str):
            specs = [(sort_spec, direction)]
        elif isinstance(sort_spec, tuple):
            specs = [sort_spec]
        else:
            specs = list(sort_spec)
        for key, order in reversed(specs):
            self._documents.sort(key=lambda item: item.get(key), reverse=order < 0)
        return self

    def skip(self, value: int):
        self._skip = max(0, value)
        return self

    def limit(self, value: int):
        self._limit = max(0, value)
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        end_limit = length if length is not None else self._limit
        sliced = self._documents[self._skip :]
        if end_limit is not None:
            sliced = sliced[:end_limit]
        return [copy.deepcopy(item) for item in sliced]


class InMemoryAggregateCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        rows = [copy.deepcopy(item) for item in self._documents]
        return rows[:length] if length is not None else rows


class InMemoryCollection:
    def __init__(self) -> None:
        self.documents: dict[str, dict[str, Any]] = {}
        self.indexes: list[tuple[Any, dict[str, Any]]] = []

    async def create_index(self, keys: Any, **kwargs: Any) -> str:
        self.indexes.append((keys, kwargs))
        return str(kwargs.get("name") or keys)

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        stored = copy.deepcopy(document)
        document_id = str(stored.get("_id") or stored.get("id"))
        stored["_id"] = document_id
        stored.setdefault("id", document_id)
        if document_id in self.documents:
            from pymongo.errors import DuplicateKeyError
            raise DuplicateKeyError(f"Document with _id={document_id} already exists")
        self.documents[document_id] = stored
        return InsertOneResult(inserted_id=document_id)

    async def insert_many(self, documents: list[dict[str, Any]]) -> None:
        for document in documents:
            await self.insert_one(document)

    async def find_one(
        self,
        filter: dict[str, Any] | None = None,
        projection: dict[str, int] | None = None,
    ) -> dict[str, Any] | None:
        for document in self.documents.values():
            if matches_filter(document, filter or {}):
                return project_document(copy.deepcopy(document), projection)
        return None

    def find(
        self,
        filter: dict[str, Any] | None = None,
        projection: dict[str, int] | None = None,
    ) -> InMemoryCursor:
        rows = [
            project_document(copy.deepcopy(document), projection)
            for document in self.documents.values()
            if matches_filter(document, filter or {})
        ]
        return InMemoryCursor(rows)

    def aggregate(self, pipeline: list[dict[str, Any]]) -> InMemoryAggregateCursor:
        return InMemoryAggregateCursor(apply_aggregate_pipeline(list(self.documents.values()), pipeline))

    async def count_documents(self, filter: dict[str, Any] | None = None) -> int:
        return sum(
            1
            for document in self.documents.values()
            if matches_filter(document, filter or {})
        )

    async def update_one(
        self,
        filter: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> UpdateResult:
        for document_id, document in self.documents.items():
            if matches_filter(document, filter):
                apply_update(document, update)
                self.documents[document_id] = document
                return UpdateResult(matched_count=1, modified_count=1)
        if not upsert:
            return UpdateResult(matched_count=0, modified_count=0)
        new_document = build_upsert_document(filter, update)
        result = await self.insert_one(new_document)
        return UpdateResult(matched_count=0, modified_count=0, upserted_id=result.inserted_id)

    async def update_many(self, filter: dict[str, Any], update: dict[str, Any]) -> UpdateResult:
        matched_count = 0
        for document_id, document in self.documents.items():
            if matches_filter(document, filter):
                apply_update(document, update)
                self.documents[document_id] = document
                matched_count += 1
        return UpdateResult(matched_count=matched_count, modified_count=matched_count)

    async def find_one_and_update(
        self,
        filter: dict[str, Any],
        update: dict[str, Any],
        projection: dict[str, int] | None = None,
        return_document: bool = False,
    ) -> dict[str, Any] | None:
        for document_id, document in self.documents.items():
            if matches_filter(document, filter):
                original = copy.deepcopy(document)
                apply_update(document, update)
                self.documents[document_id] = document
                if return_document:
                    return project_document(self.documents[document_id], projection)
                return project_document(original, projection)
        return None

    async def delete_one(self, filter: dict[str, Any]) -> DeleteResult:
        for document_id, document in list(self.documents.items()):
            if matches_filter(document, filter):
                del self.documents[document_id]
                return DeleteResult(deleted_count=1)
        return DeleteResult(deleted_count=0)

    async def delete_many(self, filter: dict[str, Any]) -> DeleteResult:
        deleted_count = 0
        for document_id, document in list(self.documents.items()):
            if matches_filter(document, filter):
                del self.documents[document_id]
                deleted_count += 1
        return DeleteResult(deleted_count=deleted_count)

    async def drop(self) -> None:
        self.documents.clear()
        self.indexes.clear()

    async def command(self, command_name: str) -> dict[str, int]:
        return {"ok": 1}


class InMemoryDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, InMemoryCollection] = {}

    def __getitem__(self, name: str) -> InMemoryCollection:
        return self._collections.setdefault(name, InMemoryCollection())

    def __getattr__(self, name: str) -> InMemoryCollection:
        if name.startswith("_"):
            raise AttributeError(name)
        return self[name]

    async def command(self, command_name: str) -> dict[str, int]:
        return {"ok": 1}


def project_document(
    document: dict[str, Any] | None,
    projection: dict[str, int] | None,
) -> dict[str, Any] | None:
    if document is None or projection is None:
        return document
    include = {key for key, value in projection.items() if value}
    exclude = {key for key, value in projection.items() if not value}
    if include:
        projected = {key: document[key] for key in include if key in document}
        if projection.get("_id", 1) and "_id" in document:
            projected["_id"] = document["_id"]
        return projected
    for key in exclude:
        document.pop(key, None)
    return document


def matches_filter(document: dict[str, Any], filter: dict[str, Any]) -> bool:
    for key, expected in filter.items():
        if key == "$text":
            raw_search = str((expected or {}).get("$search") or "").strip().lower()
            if not raw_search:
                continue
            haystack = " ".join(_flatten_text_values(document)).lower()
            terms = [term for term in re.split(r"\s+", raw_search) if term]
            if not all(term in haystack for term in terms):
                return False
            continue
        if key == "$or":
            if not any(matches_filter(document, option) for option in expected):
                return False
            continue
        if key == "$and":
            if not all(matches_filter(document, option) for option in expected):
                return False
            continue
        actual = document.get(key)
        if isinstance(expected, dict):
            if "$exists" in expected:
                exists = key in document
                if bool(expected["$exists"]) != exists:
                    return False
            elif "$regex" in expected:
                flags = re.IGNORECASE if "i" in str(expected.get("$options", "")) else 0
                if not re.search(str(expected["$regex"]), str(actual or ""), flags):
                    return False
            elif "$ne" in expected:
                if actual == expected["$ne"]:
                    return False
            elif "$in" in expected:
                if actual not in expected["$in"]:
                    return False
            elif "$nin" in expected:
                if actual in expected["$nin"]:
                    return False
            elif "$gt" in expected:
                if actual is None or actual <= expected["$gt"]:
                    return False
            elif "$gte" in expected:
                if actual is None or actual < expected["$gte"]:
                    return False
            elif "$lt" in expected:
                if actual is None or actual >= expected["$lt"]:
                    return False
            elif "$lte" in expected:
                if actual is None or actual > expected["$lte"]:
                    return False
            else:
                return False
        elif isinstance(actual, list):
            if expected not in actual:
                return False
        elif actual != expected:
            return False
    return True


def apply_aggregate_pipeline(documents: list[dict[str, Any]], pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [copy.deepcopy(document) for document in documents]
    for stage in pipeline:
        if "$match" in stage:
            rows = [row for row in rows if matches_filter(row, stage["$match"])]
        elif "$sort" in stage:
            for key, order in reversed(list(stage["$sort"].items())):
                rows.sort(key=lambda item: item.get(key), reverse=order < 0)
        elif "$limit" in stage:
            rows = rows[: max(0, int(stage["$limit"]))]
        elif "$project" in stage:
            rows = [project_document(row, stage["$project"]) or {} for row in rows]
        elif "$count" in stage:
            rows = [{stage["$count"]: len(rows)}] if rows else []
        elif "$facet" in stage:
            rows = [
                {
                    name: apply_aggregate_pipeline(rows, facet_pipeline)
                    for name, facet_pipeline in stage["$facet"].items()
                }
            ]
        else:
            raise NotImplementedError(f"Unsupported in-memory aggregate stage: {stage}")
    return rows


def _flatten_text_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_flatten_text_values(item))
        return values
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(_flatten_text_values(item))
        return values
    if isinstance(value, (str, int, float)):
        return [str(value)]
    return []


def apply_update(document: dict[str, Any], update: dict[str, Any]) -> None:
    for key, value in update.get("$set", {}).items():
        document[key] = value
    for key in update.get("$unset", {}):
        document.pop(key, None)
    for key, value in update.get("$setOnInsert", {}).items():
        document.setdefault(key, value)
    for key, value in update.get("$inc", {}).items():
        document[key] = document.get(key, 0) + value
    for key, value in update.get("$pull", {}).items():
        current = document.get(key)
        if isinstance(current, list):
            document[key] = [item for item in current if item != value]
    for key, value in update.get("$addToSet", {}).items():
        current = document.setdefault(key, [])
        if isinstance(current, list) and value not in current:
            current.append(value)
    for key, value in update.get("$push", {}).items():
        current = document.setdefault(key, [])
        if isinstance(current, list):
            current.append(value)


def build_upsert_document(filter: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    document = {key: value for key, value in filter.items() if not key.startswith("$")}
    apply_update(document, {"$set": update.get("$setOnInsert", {})})
    apply_update(document, {"$set": update.get("$set", {})})
    return document
