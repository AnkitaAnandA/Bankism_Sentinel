"""Production-mode verification launcher; keys are random, never printed or persisted."""

import os
import secrets
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
runtime = root / "runtime"
runtime.mkdir(exist_ok=True)
env = os.environ.copy()
env.update(
    ENV="production",
    INTENT_HMAC_KEY=secrets.token_hex(32),
    SESSION_SIGNING_KEY=secrets.token_hex(32),
    ALLOWED_ORIGINS="http://localhost:4173,http://127.0.0.1:4173",
    DATABASE_URL="sqlite:///" + str(runtime / "production.db"),
    RATE_LIMIT_PER_MINUTE="10000",
    PORT="8000",
    LLM_PROVIDER="mock",
)
subprocess.run(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        env["PORT"],
        "--workers",
        "1",
    ],
    cwd=root / "backend",
    env=env,
    check=True,
)
