from datetime import UTC, datetime

from fastapi.testclient import TestClient


def sample_payload(total_tokens: int = 33269) -> dict:
    today = datetime.now(UTC).date().isoformat()
    return {
        "user_id": "jun",
        "source": "claude-code",
        "hostname": "devbox",
        "ccusage": {
            "projects": {
                "token-usage-backend": [
                    {
                        "date": today,
                        "inputTokens": 277,
                        "outputTokens": 31456,
                        "cacheCreationTokens": 512,
                        "cacheReadTokens": 1024,
                        "totalTokens": total_tokens,
                        "totalCost": 17.58,
                        "modelsUsed": ["gpt-5-codex"],
                        "breakdown": {
                            "gpt-5-codex": {
                                "inputTokens": 277,
                                "outputTokens": 31456,
                                "cacheCreationTokens": 512,
                                "cacheReadTokens": 1024,
                                "totalTokens": total_tokens,
                                "costUSD": 17.58,
                            }
                        },
                    }
                ]
            }
        },
    }


def test_collect_inserts_and_upserts_by_user_date_project_source(client: TestClient) -> None:
    first = client.post("/api/collect", json=sample_payload())
    assert first.status_code == 202
    assert first.json()["inserted"] == 1

    second = client.post("/api/collect", json=sample_payload(total_tokens=50000))
    assert second.status_code == 202
    assert second.json()["updated"] == 1

    daily = client.get("/api/usage/daily", params={"userId": "jun"})
    assert daily.status_code == 200
    assert daily.json()[0]["totalTokens"] == 50000


def test_reports_alias_accepts_public_upload(client: TestClient) -> None:
    response = client.post("/api/reports", json=sample_payload())
    assert response.status_code == 202
    assert response.json()["accepted"] == 1

