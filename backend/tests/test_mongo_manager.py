import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.database.mongo_manager import ensure_mongo_indexes


class MongoManagerTests(unittest.TestCase):
    def test_ensure_indexes_creates_expected_scan_session_indexes(self):
        collection = MagicMock()
        collection.create_index = AsyncMock()
        database = {"scan_sessions": collection}
        with patch("app.infrastructure.database.mongo_manager.get_database", return_value=database):
            asyncio.run(ensure_mongo_indexes())

        created_names = [call.kwargs.get("name") for call in collection.create_index.call_args_list]
        self.assertIn("idx_scan_sessions_updated_at_desc", created_names)
        self.assertIn("idx_scan_sessions_status_updated_at_desc", created_names)
        self.assertIn("idx_scan_sessions_repo_updated_at_desc", created_names)


if __name__ == "__main__":
    unittest.main()
