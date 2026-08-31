from __future__ import annotations

import os

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("APP_NAME", "CodeGuard-Test")
os.environ.setdefault("ARTIFACTS_DIR", os.path.join(os.environ.get("TEMP", "/tmp"), "codeguard_test_artifacts"))
