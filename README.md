# 주식 실적·뉴스 분석

트레이딩뷰 이미지로 종목을 분석할 때의 규칙과 엑셀 양식, 미국 상장기업의 공시·시세·뉴스 수집 도구를 보관합니다. 기존 [분석 규칙](AGENTS.md)을 따릅니다.

## 이미지를 올려 분석하기: API 키 불필요

ChatGPT 또는 이 저장소에 연결된 코딩 도우미에게 다음 자료를 올립니다.

1. 종목명과 원하는 분기 수(21개 또는 22개).
2. 트레이딩뷰의 희석 EPS·매출·영업이익·잉여현금흐름·희석주식수·ROE·BPS 화면. **TTM 계산을 위해 요청 분기보다 3개 이전 분기까지** 보이도록 합니다.
3. 예: `DXCM 22개 분기. 기존 양식의 엑셀과 상세 보고서를 만들어줘.`

도우미가 이미지를 읽고 값을 검토해 기존 엑셀 양식으로 정리하며, 회사 공시·실적 발표와 대조한 한국어 보고서를 작성합니다. 보고서에는 기존의 **5개 항목 각 20점과 총점**, 목표가 계산의 근거와 가정, 공시와 화면의 수치 차이 추적 결과가 포함됩니다. 4분기 열을 색으로 강조합니다. 기존 엑셀 원본은 수정하지 않습니다.

이 대화에서 도우미가 이미지를 읽는 방식은 **별도의 OpenAI API 키를 요구하지 않습니다.** 다만 이용 중인 ChatGPT·도우미 서비스의 요금제와 사용 한도는 별도로 적용될 수 있습니다. 이 저장소만 GitHub에 올렸다고 해서 이미지가 자동으로 읽히거나 보고서가 만들어지는 것은 아닙니다. 아래 자동 수집 프로그램 및 선택적인 API 분석은 별도 기능입니다.

### 검토된 이미지 값을 엑셀에 넣는 도구

도우미가 이미지 값을 [examples/분기입력.csv](examples/분기입력.csv)의 열 형식으로 전사·확인한 후 아래처럼 실행할 수 있습니다. 매출·영업이익·FCF·희석주식수는 **백만 단위**, EPS와 BPS는 달러, ROE는 퍼센트 숫자로 넣습니다. 화면에서 B 단위로 반올림된 값은 원래 정밀도를 구별할 수 있도록 보고서에 적어야 합니다.

```bash
python -m pip install -r requirements.txt
python -m stock_research.workbook DXCM 입력.csv DXCM_22분기.xlsx --quarters 22
```

CSV는 오래된 분기부터 25행(선행 3분기 + 분석 22분기)을 넣습니다. 21분기는 `--quarters 21`과 24행을 사용합니다. `earnings_date`, `close_usd`, `next_date`, `next_close_usd`, `filing_url`은 확인된 경우 입력하고 미확인이면 비웁니다. **이 도구는 이미지 OCR과 PDF 보고서 생성 기능이 아닙니다.** 생성된 수식은 Excel 또는 LibreOffice에서 열어 다시 계산합니다.

## 지금 할 수 있는 것

- SEC 회사 정보, 10-K·10-Q·8-K 등 공시 링크와 직접 공시된 분기 재무 수치를 수집합니다.
- Yahoo Finance의 **비수정 일별 종가**와 Google News의 뉴스 제목·링크를 모읍니다. 뉴스 원문과 사실관계는 별도로 확인해야 합니다.
- 선택적으로 OpenAI API로 한국어 분석 초안을 생성합니다. API 키를 설정하지 않으면 외부 AI 호출 없이 자료만 수집합니다.
- GitHub Actions에서 수동 또는 평일 자동으로 실행하고 결과를 다운로드할 수 있습니다.

이 자동 수집 기능은 위의 이미지 입력과 별개이며, **이미지만으로 PDF 보고서를 자동 생성하지 않습니다.** 직접 분기 단위로 제공되지 않은 현금흐름, 4분기 EPS 등은 빈 값으로 남깁니다. 22개 분기 모두가 채워진다고 보장하지 않으며, 단일 분기와 누적 수치를 혼동하지 않도록 합니다. 생성된 문서의 수치·점수·출처는 투자 판단 전에 원문과 대조해야 합니다.

## 내 컴퓨터에서 실행

Python 3.11 이상이 필요합니다. 저장소 폴더에서 터미널을 열고 실행합니다. 공시·시세 수집에는 추가 패키지가 필요하지 않습니다. 엑셀 생성에는 위의 `openpyxl` 설치가 필요합니다.

```bash
python -m stock_research DXCM
```

관심 종목을 [config/watchlist.txt](config/watchlist.txt)에 한 줄씩 넣으면 종목을 생략해도 됩니다.

```bash
python -m stock_research
```

결과는 `output/티커/기준일/` 안의 `data.json`과 `report.md`에 저장됩니다. 과거 기준일은 `--as-of 2026-11-06`처럼 지정할 수 있습니다. SEC 공시와 시세는 해당 날짜 이후의 데이터를 제외합니다. **뉴스 검색 결과는 실행 시점 기준**이므로 과거 시점으로 돌아간 뉴스가 아닙니다.

SEC는 연락 가능한 사용자 식별 정보를 요구합니다. 환경변수 `SEC_USER_AGENT`를 `이름 이메일주소` 형태로 설정하세요. 예를 들어 PowerShell에서는 다음과 같습니다.

```powershell
$env:SEC_USER_AGENT = 'MyResearch 내이메일@example.com'
python -m stock_research DXCM
```

## 선택: AI 분석

AI 사용은 별도 API 계정·키가 필요하고 사용량에 따라 비용이 발생할 수 있습니다. ChatGPT 구독과 API 사용료는 별도일 수 있습니다. OpenAI 키를 파일이나 GitHub 코드에 올리지 마세요.

```powershell
$env:OPENAI_API_KEY = '발급받은_API_키'
python -m stock_research DXCM --ai
```

기본 모델은 `gpt-4.1-mini`이며 `--model` 또는 `OPENAI_MODEL`로 변경할 수 있습니다. AI가 산출한 점수나 목표가를 사실로 보지 말고 근거를 검토하세요. AI에게 수집한 공시·뉴스 제목이 전송됩니다.

## GitHub에서 실행

1. GitHub 저장소의 **Settings → Secrets and variables → Actions**에서 Variables에 `SEC_USER_AGENT`를 연락 가능한 이름과 이메일로 등록합니다.
2. AI까지 사용할 때만 Secrets에 `OPENAI_API_KEY`를 등록합니다. 정기 실행에도 AI 분석을 포함하려면 Variables에 `AI_ANALYSIS_ENABLED`를 `true`로 설정합니다.
3. **Actions → Stock research → Run workflow**에서 티커를 넣고 실행합니다. AI 분석은 체크한 경우에만 실행됩니다.
4. 실행 결과 화면 아래 **Artifacts**에서 생성된 자료를 내려받습니다. 보관 기간은 30일입니다.

자동 수집은 월~금 22:00 UTC에 실행됩니다. 한국 시간으로 화~토 오전 7시이며 통상 미국 정규장 마감 후입니다. 휴장일에는 직전 거래일 종가가 표시될 수 있습니다. 자동 AI 분석은 기본적으로 꺼져 있으며 위 설정으로 켤 수 있습니다. GitHub Actions가 지연될 수 있고 실행 시간·저장 공간 한도는 GitHub 정책과 계정에 따라 다릅니다.

데이터 소스가 실패하면 가능한 자료와 오류가 함께 저장되고 실행은 실패로 표시됩니다. 외부 데이터 제공자는 접근을 제한하거나 형식을 바꿀 수 있습니다.

## 검증

```bash
python -m unittest discover -s tests -v
```
