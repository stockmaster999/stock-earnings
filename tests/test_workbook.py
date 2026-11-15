import csv
import tempfile
import unittest
from pathlib import Path

import openpyxl

from stock_research.workbook import FIELDS, build, load_rows


class WorkbookTests(unittest.TestCase):
    def make_csv(self, path, count):
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["quarter", *FIELDS])
            writer.writeheader()
            for i in range(count + 3):
                year = 2020 + (i + 2) // 4
                quarter = (i + 2) % 4 + 1
                writer.writerow({"quarter": f"{year}Q{quarter}", "eps": 1, "revenue_m": 100,
                                 "operating_income_m": 10, "free_cash_flow_m": 5,
                                 "diluted_shares_m": 20, "roe_pct": 3, "bps": 4})

    def test_21_and_22_quarters_preserve_layout_and_highlight_q4(self):
        for count in (21, 22):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "data.csv"
                output = Path(tmp) / "report.xlsx"
                self.make_csv(path, count)
                rows = load_rows(path, count)
                build("TEST", rows, output, count)
                wb = openpyxl.load_workbook(output)
                sheet = wb.active
                self.assertEqual(sheet.max_column, count + 1)
                self.assertEqual(sheet["A2"].value, "EPS (TTM)")
                self.assertTrue(sheet["B2"].value.startswith("=IF("))
                self.assertEqual(wb["TTM_계산값"]["C2"].value, 4)
                self.assertEqual(wb["TTM_계산값"]["D2"].value, 400)
                highlighted = [sheet.cell(1, i).value for i in range(2, count + 2) if sheet.cell(2, i).fill.patternType == "solid"]
                self.assertEqual(highlighted, [r["quarter"] for r in rows[3:] if r["quarter"].endswith("Q4")])
                self.assertEqual(len(wb[f"{count}분기_차트"]._charts), 4)
                with self.assertRaises(FileExistsError):
                    build("TEST", rows, output, count)

    def test_missing_quarter_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            self.make_csv(path, 22)
            text = path.read_text(encoding="utf-8").replace("2021Q2", "2021Q3", 1)
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_rows(path, 22)


if __name__ == "__main__":
    unittest.main()
