"""Cross-platform one-command local demo launcher using disposable generated keys."""

import os
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.setdefault("VITE_API_BASE_URL", "http://localhost:8000")
    npm = "npm.cmd" if os.name == "nt" else "npm"
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--workers",
                "1",
            ],
            cwd=root / "backend",
            env=env,
        ),
        subprocess.Popen([npm, "run", "dev"], cwd=root / "frontend", env=env),
    ]
    print(
        "Bankism Sentinel: http://localhost:5173 (synthetic demo). Ctrl+C stops both servers."
    )
    try:
        processes[0].wait()
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            else:
                process.terminate()
        for process in processes:
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
