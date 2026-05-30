from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def seed_usage(client: TestClient) -> None:
    today = datetime.now(UTC).date()
    payload = {
        "user_id": "team",
        "source": "codex",
        "ccusage": {
            "projects": {
                "backend": [
                    {
                        "date": today.isoformat(),
                        "inputTokens": 100,
                        "outputTokens": 200,
                        "cacheCreationTokens": 50,
                        "cacheReadTokens": 25,
                        "totalTokens": 375,
                        "totalCost": 1.25,
                        "modelsUsed": ["gpt-5-codex"],
                    }
                ],
                "frontend": [
                    {
                        "date": (today - timedelta(days=1)).isoformat(),
                        "inputTokens": 400,
                        "outputTokens": 600,
                        "cacheCreationTokens": 0,
                        "cacheReadTokens": 0,
                        "totalTokens": 1000,
                        "totalCost": 2.50,
                        "modelsUsed": ["claude-sonnet"],
                    }
                ],
            }
        },
    }
    response = client.post("/api/collect", json=payload)
    assert response.status_code == 202


def test_summary_projects_sources_and_models(client: TestClient) -> None:
    seed_usage(client)

    summary = client.get("/api/summary", params={"userId": "team"})
    assert summary.status_code == 200
    assert summary.json()["totalTokens"] == 1375
    assert summary.json()["costUsd"] == 3.75

    projects = client.get("/api/usage/projects", params={"userId": "team"}).json()
    assert {row["name"] for row in projects} == {"backend", "frontend"}

    sources = client.get("/api/usage/sources", params={"userId": "team"}).json()
    assert sources[0]["name"] == "codex"
    assert sources[0]["total_tokens"] == 1375

    models = client.get("/api/usage/models", params={"userId": "team"}).json()
    assert {row["model"] for row in models} == {"gpt-5-codex", "claude-sonnet"}


def test_users_endpoint_is_public(client: TestClient) -> None:
    seed_usage(client)
    users = client.get("/api/users")
    assert users.status_code == 200
    assert users.json() == [{"id": "team", "name": "team", "githubUsername": "team"}]

