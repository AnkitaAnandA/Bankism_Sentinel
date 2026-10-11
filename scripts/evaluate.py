import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.config import Settings
from app.security.evaluation import Evaluator


async def main():
    result = await Evaluator(Settings()).run()
    serialized = [r.model_dump() for r in result]
    output = Path(__file__).resolve().parents[1] / "reports"
    output.mkdir(exist_ok=True)
    (output / "evaluation.json").write_text(
        json.dumps(serialized, indent=2), encoding="utf-8"
    )
    print(json.dumps(serialized, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
