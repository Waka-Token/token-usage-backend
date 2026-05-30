from datetime import UTC, datetime

from fastapi.testclient import TestClient


def test_badge_returns_public_svg(client: TestClient) -> None:
    today = datetime.now(UTC).date().isoformat()
    client.post(
        "/api/collect",
        json={
            "user_id": "jun",
            "source": "opencode",
            "ccusage": {
                "projects": {
                    "token-usage-backend": [
                        {
                            "date": today,
                            "inputTokens": 1000,
                            "outputTokens": 2000,
                            "cacheCreationTokens": 0,
                            "cacheReadTokens": 0,
                            "totalTokens": 3000,
                            "totalCost": 0.42,
                            "modelsUsed": ["gpt-5-codex"],
                        }
                    ]
                }
            },
        },
    )

    response = client.get("/api/badge.svg", params={"userId": "jun", "type": "monthly", "style": "flat"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "max-age=300"
    assert "<svg" in response.text
    assert "tokens" in response.text


def test_badge_without_data_still_returns_svg(client: TestClient) -> None:
    response = client.get("/badge/missing.svg", params={"type": "total"})
    assert response.status_code == 200
    assert "no data" in response.text

