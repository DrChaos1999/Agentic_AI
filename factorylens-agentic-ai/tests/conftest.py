from __future__ import annotations

import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_factorylens.db")
