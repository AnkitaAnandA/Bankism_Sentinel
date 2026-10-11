import argparse
import asyncio
import json
import time
import uuid
from pathlib import Path
import httpx


def stats(samples, duration, count):
    ordered = sorted(samples)

    def percentile(p):
        return round(ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p))], 3)

    return {
        "samples": count,
        "p50_ms": percentile(0.5),
        "p95_ms": percentile(0.95),
        "p99_ms": percentile(0.99),
        "requests_per_second": round(count / duration, 2),
    }


async def run(url, n):
    async with httpx.AsyncClient(base_url=url, timeout=90) as client:
        token = (await client.post("/api/demo/session/alice", json={})).json()[
            "demo_token"
        ]
        client.headers["Authorization"] = "Bearer " + token
        result = {}
        for endpoint in ["analyze", "prepare", "execute"]:
            samples = []
            started = time.perf_counter()
            for _ in range(n):
                if endpoint == "execute":
                    p = (
                        await client.post(
                            "/api/intents/prepare",
                            json={"message": "Transfer ₹1 to Rahul"},
                        )
                    ).json()
                    assert p["intent_id"], p
                    r = await client.post(
                        "/api/intents/" + p["intent_id"] + "/confirm",
                        json={"integrity_tag": p["transaction"]["integrity_tag"]},
                    )
                    assert r.status_code == 200, r.text
                tick = time.perf_counter()
                if endpoint == "analyze":
                    r = await client.post(
                        "/api/firewall/analyze",
                        json={"message": "Show my account balance"},
                    )
                elif endpoint == "prepare":
                    r = await client.post(
                        "/api/intents/prepare", json={"message": "Transfer ₹1 to Rahul"}
                    )
                else:
                    r = await client.post(
                        "/api/transfers/execute",
                        json={
                            "intent_id": p["intent_id"],
                            "idempotency_key": uuid.uuid4().hex,
                        },
                    )
                samples.append((time.perf_counter() - tick) * 1000)
                assert r.status_code == 200, r.text
                if endpoint == "execute":
                    assert r.json()["execution_allowed"], r.text
            result[endpoint] = stats(samples, time.perf_counter() - started, n)
        result["methodology"] = (
            "Sequential localhost HTTP; execute throughput includes preparation and confirmation; default samples 100. Run against isolated disposable demo data with elevated test quota."
        )
        path = Path(__file__).resolve().parents[1] / "reports"
        path.mkdir(exist_ok=True)
        (path / "load.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("url", nargs="?", default="http://localhost:8000")
    p.add_argument("--samples", type=int, default=100)
    args = p.parse_args()
    asyncio.run(run(args.url, args.samples))
