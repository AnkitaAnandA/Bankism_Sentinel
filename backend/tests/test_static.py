from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_single_service_static_and_api(tmp_path):
    cfg = Settings(
        database_url=f"sqlite:///{tmp_path}/single.db",
        intent_hmac_key="a" * 64,
        session_signing_key="b" * 64,
        serve_frontend=True,
    )
    directory = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    assert (
        directory / "index.html"
    ).exists(), "Build frontend before static integration verification"
    with TestClient(create_app(cfg)) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "Bankism Sentinel" in page.text
        assert page.headers["content-type"].startswith("text/html")
        asset = next((directory / "assets").glob("*.js"))
        assert client.get("/assets/" + asset.name).status_code == 200
        assert client.get("/health").json()["verdict"] == "ALLOW"
        login = client.post("/api/demo/session/alice").json()
        accounts = client.get(
            "/api/accounts/balance",
            headers={"Authorization": "Bearer " + login["demo_token"]},
        ).json()
        assert accounts["approved"]
        assert len(accounts["accounts"]) == 2
