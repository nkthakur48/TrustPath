from fastapi.testclient import TestClient

from app.graph.chat import build_chat_graph, get_chat_graph
from app.main import app
from app.services import openrouter


def test_chat_keeps_thread_history(monkeypatch):
    seen = []
    replies = iter(["Hello!", "You said hi earlier."])

    def fake_completion(messages):
        seen.append(messages)
        return next(replies)

    monkeypatch.setattr(openrouter, "complete_chat", fake_completion)
    graph = build_chat_graph()
    app.dependency_overrides[get_chat_graph] = lambda: graph
    try:
        client = TestClient(app)
        first = client.post("/api/v1/chat", json={"message": "hi"}).json()
        assert first["reply"] == "Hello!"

        second = client.post("/api/v1/chat", json={"message": "what did I say?", "thread_id": first["thread_id"]}).json()
        assert second["reply"] == "You said hi earlier."
        assert [m["role"] for m in seen[1]] == ["system", "user", "assistant", "user"]
    finally:
        app.dependency_overrides.clear()


def test_chat_without_key_returns_503():
    app.dependency_overrides[get_chat_graph] = build_chat_graph
    try:
        assert TestClient(app).post("/api/v1/chat", json={"message": "hi"}).status_code == 503
    finally:
        app.dependency_overrides.clear()
