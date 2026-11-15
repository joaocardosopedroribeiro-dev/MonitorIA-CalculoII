"""Gera automaticamente arquivos de relatório a partir das métricas locais.

Exemplo: python scripts/gerar_relatorio.py
O script pode ser agendado pelo sistema operacional ou por um orquestrador.
"""
from pathlib import Path
import sys
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from storage import create_report, export_csv, load_events  # noqa: E402


def main():
    events = load_events(ROOT / "data" / "events.sqlite3")
    out = ROOT / "exports"
    out.mkdir(exist_ok=True)
    report_path = out / f"relatorio_{date.today().isoformat()}.md"
    csv_path = out / "monitoria_indicadores.csv"
    report_path.write_text(create_report(events), encoding="utf-8")
    csv_path.write_text(export_csv(events), encoding="utf-8-sig")
    print(f"Relatório: {report_path}\nCSV: {csv_path}\nRegistros: {len(events)}")


if __name__ == "__main__":
    main()
