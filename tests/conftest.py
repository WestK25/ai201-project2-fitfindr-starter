import pytest
import agent
import trends
from datetime import datetime, timezone

@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch, tmp_path):
    monkeypatch.setenv("FITFINDR_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(trends, "_now", lambda: datetime(2026, 10, 2, tzinfo=timezone.utc))
    monkeypatch.setattr(agent, "get_trends", lambda item: {"status": "unavailable", "relevant_trend": None})
