import json
from datetime import datetime, timezone
from pathlib import Path


def log_execution(event: str, model: str | None = None, status: str = "ok") -> None:
    """Registra metadados seguros, sem texto, credenciais ou identificadores pessoais."""
    directory = Path("/persistent")
    try:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "execucoes.json"
    except OSError:
        directory = Path.cwd() / "logs"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "execucoes.json"

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
        "status": status,
        "model": model,
    }

    records = []
    if path.exists():
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                records = []
        except (json.JSONDecodeError, OSError):
            records = []

    records.insert(0, record)
    try:
        path.write_text(
            json.dumps(records[:100], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass
