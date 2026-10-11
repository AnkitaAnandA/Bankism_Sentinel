import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.config import Settings
from app.data.seed import seed
from app.models.database import Database
from app.banking.intent_parser import parse
from app.security.normalizer import normalize
from app.security.rule_detector import detect
from app.security.policy_engine import check_policy

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    cfg = Settings(
        database_url=f"sqlite:///{directory}/core.db",
        intent_hmac_key=secrets.token_hex(32),
        session_signing_key=secrets.token_hex(32),
    )
    db = Database(cfg.database_url)
    seed(db)
    samples = []
    for _ in range(500):
        tick = time.perf_counter()
        text = "Transfer ₹500 to Rahul"
        n = normalize(text)
        detect(n)
        p = parse(text)
        with db.sessions() as s:
            check_policy(
                s, cfg, "alice", "alice-checking", "payee-rahul", p.amount_minor, "INR"
            )
        samples.append((time.perf_counter() - tick) * 1000)
    db.engine.dispose()
    env = os.environ.copy()
    env.update(
        ENV="production",
        INTENT_HMAC_KEY=secrets.token_hex(32),
        SESSION_SIGNING_KEY=secrets.token_hex(32),
        DATABASE_URL=f"sqlite:///{directory}/cold.db",
        ALLOWED_ORIGINS="http://localhost:4173",
        LLM_PROVIDER="mock",
    )
    tick = time.perf_counter()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
            "--workers",
            "1",
        ],
        cwd=root / "backend",
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        with httpx.Client(timeout=0.5) as c:
            for _ in range(100):
                try:
                    if c.get("http://127.0.0.1:8001/health").status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.02)
            else:
                raise RuntimeError("Cold-start readiness failed")
        cold = (time.perf_counter() - tick) * 1000
    finally:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            process.terminate()
        process.wait(timeout=10)
    values = sorted(samples)
    result = {
        "deterministic_samples": len(samples),
        "deterministic_p50_ms": round(values[249], 3),
        "deterministic_p95_ms": round(values[474], 3),
        "deterministic_p99_ms": round(values[494], 3),
        "local_cold_start_ms": round(cold, 3),
        "methodology": "Normalizer + rules + parser + real SQLAlchemy policy reads; cold start includes fresh tables/seeding/import and first HTTP health response, one local process.",
    }
    out = root / "reports"
    out.mkdir(exist_ok=True)
    (out / "core.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
