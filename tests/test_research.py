import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stock_research import app


class ResearchTests(unittest.TestCase):
    def test_quarter_data_respects_known_date_and_excludes_cumulative(self):
        facts = {"facts": {"us-gaap": {"OperatingIncomeLoss": {"units": {"USD": [
            {"start": "2026-01-01", "end": "2026-03-31", "val": 50, "form": "10-Q", "filed": "2026-05-01"},
            {"start": "2026-01-01", "end": "2026-03-31", "val": 55, "form": "10-Q", "filed": "2027-01-01"},
            {"start": "2026-01-01", "end": "2026-06-30", "val": 100, "form": "10-Q", "filed": "2026-08-01"},
        ]}}}}}
        actual = app.quarter_fact(facts, ("OperatingIncomeLoss",), unit="USD", as_of="2026-11-01")
        self.assertEqual([(x["end"], x["value"]) for x in actual], [("2026-03-31", 50)])

    def test_failed_sources_are_recorded_and_exit_nonzero(self):
        with tempfile.TemporaryDirectory() as path, \
             patch.object(app, "sec_data", side_effect=OSError("unavailable")), \
             patch.object(app, "price_data", return_value={"source": "test", "url": "https://example.com", "latest": {"date": "2026-11-06", "close_usd": 10}}), \
             patch.object(app, "news_data", return_value={"items": []}):
            code = app.main(["DXCM", "--as-of", "2026-11-06", "--output", path])
            bundle = json.loads((Path(path) / "DXCM/2026-11-06/data.json").read_text())
            report = (Path(path) / "DXCM/2026-11-06/report.md").read_text()
        self.assertEqual(code, 1)
        self.assertIn("sec", bundle["errors"])
        self.assertIn("unavailable", report)
        self.assertIn("$10.00", report)

    def test_rejects_untrusted_ticker_path(self):
        with self.assertRaises(ValueError):
            app.normalize_ticker("../etc/passwd")


if __name__ == "__main__":
    unittest.main()
