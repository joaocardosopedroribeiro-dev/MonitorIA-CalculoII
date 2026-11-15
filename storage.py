"""Métricas anônimas: nunca salva nome, e-mail ou texto das perguntas."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import csv
from io import StringIO
from pathlib import Path
import sqlite3


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            topic TEXT NOT NULL,
            mode TEXT NOT NULL,
            found_sources INTEGER NOT NULL
        )""")


def log_event(db_path: Path, topic: str, mode: str, found_sources: int) -> None:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO events (timestamp, topic, mode, found_sources) VALUES (?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), topic, mode, found_sources),
        )


def load_events(db_path: Path) -> list[dict]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        result = conn.execute(
            "SELECT timestamp, topic, mode, found_sources FROM events ORDER BY timestamp DESC"
        ).fetchall()
    return [dict(row) for row in result]


def build_stats(events: list[dict]) -> dict:
    total = len(events)
    by_topic = Counter(e["topic"] for e in events)
    by_day = Counter(str(e["timestamp"])[:10] for e in events)
    with_sources = sum(int(e["found_sources"]) > 0 for e in events)
    return {
        "total": total,
        "topic_counts": dict(by_topic.most_common()),
        "day_counts": dict(sorted(by_day.items())),
        "with_sources": with_sources,
        "coverage_percent": round(100 * with_sources / total, 1) if total else 0.0,
    }


def export_csv(events: list[dict]) -> str:
    output = StringIO()
    fields = ["timestamp", "topic", "mode", "found_sources"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows([{name: event.get(name, "") for name in fields} for event in events])
    return output.getvalue()


def create_report(events: list[dict]) -> str:
    s = build_stats(events)
    lines = [
        "# Relatório automático — MonitorIA Cálculo II",
        "",
        "Indicadores anônimos gerados a partir do banco local da aplicação.",
        "",
        f"- Total de perguntas registradas: **{s['total']}**",
        f"- Perguntas com material relacionado: **{s['with_sources']}**",
        f"- Taxa de cobertura documental: **{s['coverage_percent']}%**",
        "",
        "## Assuntos mais procurados",
    ]
    if not s["topic_counts"]:
        lines.append("Ainda não há interações registradas.")
    for topic, count in s["topic_counts"].items():
        lines.append(f"- {topic}: {count}")
    lines += ["", "## Próxima ação sugerida", "Priorizar materiais didáticos para os assuntos com mais dúvidas."]
    return "\n".join(lines) + "\n"
