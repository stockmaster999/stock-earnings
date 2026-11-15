"""Fill a copy of the existing workbook from reviewed image transcription."""
from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import re
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "22분기_TTM_양식.xlsx"
FIELDS = ("eps", "revenue_m", "operating_income_m", "free_cash_flow_m", "diluted_shares_m", "roe_pct", "bps")
QUARTER = re.compile(r"^(\d{4})Q([1-4])$")


def load_rows(path: Path, count: int) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"quarter", *FIELDS}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("CSV에 quarter 및 7개 재무 항목 열이 필요합니다.")
        rows = list(reader)
    if len(rows) != count + 3:
        raise ValueError(f"{count}개 분기와 TTM 선행 3개를 합쳐 {count + 3}개 행이 필요합니다.")
    previous = None
    for row in rows:
        match = QUARTER.fullmatch((row.get("quarter") or "").strip().upper())
        if not match:
            raise ValueError(f"분기 형식 오류: {row.get('quarter')}")
        year, q = map(int, match.groups())
        serial = year * 4 + q
        if previous is not None and serial != previous + 1:
            raise ValueError("분기는 빠짐없이 오래된 순서로 입력해야 합니다.")
        previous = serial
        row["quarter"] = f"{year}Q{q}"
        for field in (*FIELDS, "close_usd", "next_close_usd"):
            text = (row.get(field) or "").strip()
            try:
                row[field] = float(text) if text else None
            except ValueError as exc:
                raise ValueError(f"{row['quarter']} {field}: 숫자를 확인하세요.") from exc
        for field in ("earnings_date", "next_date"):
            text = (row.get(field) or "").strip()
            row[field] = dt.date.fromisoformat(text) if text else None
    return rows


def build(ticker: str, rows: list[dict], output: Path, count: int, template: Path = TEMPLATE) -> None:
    if output.exists():
        raise FileExistsError(f"기존 파일은 덮어쓰지 않습니다: {output}")
    wb = openpyxl.load_workbook(template)
    ws = wb.active
    ws.title = "종목_TTM"
    ws["A1"] = ticker
    if count == 21:
        ws.delete_cols(23)
        chart_sheet = wb["22분기_차트"]
        chart_sheet.title = "21분기_차트"
        for chart in chart_sheet._charts:
            for series in chart.series:
                for attr in ("val", "cat", "xVal", "yVal"):
                    source = getattr(series, attr, None)
                    if source:
                        for kind in ("numRef", "strRef"):
                            ref = getattr(source, kind, None)
                            if ref and ref.f:
                                ref.f = ref.f.replace("$26", "$25")
    raw = wb["원자료"]
    image = wb["이미지_원문"]
    for i, row in enumerate(rows, 2):
        for col, value in enumerate([ticker, row["quarter"], *(row[x] for x in FIELDS)], 1):
            raw.cell(i, col).value = value
            image.cell(i, col).value = value
    source_cols = {"Q1": 5, "Q2": 2, "Q3": 3, "Q4": 4}
    # Save fills before changing any column, otherwise source styles can be overwritten.
    style_fills = {q: [copy.copy(ws.cell(r, col).fill) for r in range(1, 36)] for q, col in source_cols.items()}
    for i, row in enumerate(rows[3:], 2):
        ws.cell(1, i).value = row["quarter"]
        for r, fill in enumerate(style_fills[row["quarter"][-2:]], 1):
            ws.cell(r, i).fill = copy.copy(fill)
        for r, field in ((32, "earnings_date"), (33, "close_usd"), (34, "next_date"), (35, "next_close_usd")):
            ws.cell(r, i).value = row.get(field)
        idx = i - 2
        period = rows[idx:idx + 4]
        sums = [sum(x[field] for x in period) if all(x[field] is not None for x in period) else None for field in FIELDS[:4]]
        shares = row["diluted_shares_m"]
        per_share = [v / shares if v is not None and shares else None for v in sums[1:]]
        vals = [ticker, row["quarter"], *sums, shares, *per_share, row["bps"], row["roe_pct"], row.get("earnings_date"), row.get("close_usd")]
        for col, value in enumerate(vals, 1):
            wb["TTM_계산값"].cell(i, col).value = value
        for col, value in enumerate([row["quarter"], row.get("earnings_date"), row.get("close_usd"), row.get("filing_url") or None, None, "입력값; 공시 원문 확인", None], 1):
            wb["발표일_종가_출처"].cell(i, col).value = value
        for col, value in enumerate([row["quarter"], row.get("earnings_date"), row.get("close_usd"), row.get("filing_url") or None], 1):
            wb["최초공개일_종가"].cell(i, col).value = value
    wb["자료설명"]["A1"] = "이미지에서 확인한 입력값. 화면 반올림과 공시 차이는 별도로 대조해야 합니다."
    wb["자료설명"]["A2"] = "발표일·종가 빈칸은 확인되지 않은 값입니다. 가격 조정 여부는 입력 근거에서 확인하세요."
    wb["최초공개일_종가"]["B1"] = "실적 공시일 (입력)"
    wb.calculation = openpyxl.workbook.properties.CalcProperties(calcMode="auto", fullCalcOnLoad=True, forceFullCalc=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="검토한 이미지 전사 CSV로 기존 분기 엑셀을 만듭니다.")
    parser.add_argument("ticker")
    parser.add_argument("csv", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--quarters", type=int, choices=(21, 22), default=22)
    args = parser.parse_args(argv)
    try:
        from .app import normalize_ticker
        rows = load_rows(args.csv, args.quarters)
        build(normalize_ticker(args.ticker), rows, args.output, args.quarters)
    except (OSError, ValueError) as e:
        print(f"엑셀 생성 실패: {e}", file=sys.stderr)
        return 1
    print(f"생성: {args.output} (수식은 Excel 또는 LibreOffice에서 다시 계산)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
