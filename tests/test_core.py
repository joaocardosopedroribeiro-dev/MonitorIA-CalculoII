import tempfile
import unittest
from pathlib import Path

from core import (
    Chunk, classify_topic, load_chunks, offline_answer, read_material,
    retrieve, safe_filename, split_into_chunks,
)
from storage import build_stats, create_report, export_csv, load_events, log_event


class MonitorIATests(unittest.TestCase):
    def test_retrieval_finds_relevant_source(self):
        texts = [Chunk("por_partes.md", 1, "Integração por partes usa a fórmula integral u dv = uv - integral v du."),
                 Chunk("series.md", 1, "A série geométrica converge quando valor absoluto da razão é menor que um.")]
        ranked = retrieve("Como fazer integração por partes?", texts)
        self.assertTrue(ranked)
        self.assertEqual(ranked[0].chunk.source, "por_partes.md")
        self.assertIn("por_partes.md", offline_answer(ranked))

    def test_when_no_match_does_not_invent(self):
        match = retrieve("história do cinema japonês", [Chunk("matematica.md", 1, "Integral dupla de x+y")])
        self.assertEqual(match, [])
        self.assertIn("Não encontrei", offline_answer(match))

    def test_topics(self):
        self.assertEqual(classify_topic("Como calcular uma integral dupla?"), "Integrais duplas")
        self.assertEqual(classify_topic("Convergência de séries"), "Séries e sequências")

    def test_filenames_are_sanitized(self):
        self.assertEqual(safe_filename("../../segredo.txt"), "segredo.txt")
        self.assertEqual(safe_filename("C:\\private\\doc.pdf"), "doc.pdf")

    def test_read_material_and_chunks(self):
        self.assertIn("integração", read_material("teste.txt", "integração".encode()))
        self.assertGreaterEqual(len(split_into_chunks("palavra " * 300)), 2)
        with self.assertRaises(ValueError):
            read_material("arquivo.exe", b"conteudo")

    def test_database_and_report(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "events.db"
            self.assertEqual(load_events(db), [])
            log_event(db, "Integrais duplas", "demo_sem_ia", 2)
            log_event(db, "Outros assuntos", "demo_sem_ia", 0)
            events = load_events(db)
            stats = build_stats(events)
            self.assertEqual(stats["total"], 2)
            self.assertEqual(stats["coverage_percent"], 50.0)
            self.assertIn("Integrais duplas", create_report(events))
            self.assertIn("timestamp,topic,mode,found_sources", export_csv(events))
            self.assertNotIn("email", export_csv(events))

    def test_sample_materials(self):
        folder = Path(__file__).resolve().parents[1] / "materiais"
        chunks, warnings = load_chunks(folder)
        self.assertFalse(warnings)
        self.assertGreaterEqual(len(chunks), 4)
        self.assertTrue(retrieve("derivada parcial", chunks))


if __name__ == "__main__":
    unittest.main()
