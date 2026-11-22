import pytest

from app.core.config import settings
from app.services import tools


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    monkeypatch.setattr(tools, "check_domain", lambda d: ({"resolves": True, "age_days": 3000}, f"{d}: ok"))
