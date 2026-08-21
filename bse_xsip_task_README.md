# BRS XSIP Maturity Task Automation

Single-folder Python + Playwright automation for downloading the **Matured XSIP Registration Report** from **BSE STAR MF**.

## Files

```text
bse_xsip_task/
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

```bash
python -m venv .venv
```

### Windows
```bash
.venv\Scripts\activate
```

### macOS/Linux
```bash
source .venv/bin/activate
```

## Install

```bash
pip install -r requirements.txt
playwright install
```

## Configure

Create `.env` from `.env.example` and set:
- `BSE_PASSWORD`
- update URL/selectors if needed

## Run

```bash
python main.py
```

## Output

- Downloads: `output/downloads/`
- Logs: `output/logs/`
- JSON summaries: `output/logs/`
- Failure screenshots: `output/logs/screenshots/`