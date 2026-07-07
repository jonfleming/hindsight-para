# hindsight-para

Ingest selected folders from an Obsidian vault into a Hindsight memory bank.

This project scans your vault for Markdown notes, reads each note, attaches folder context and timestamp metadata, and sends the note content to a local Hindsight server using `hindsight-client`.

## What It Does

- Scans a configured Obsidian vault path.
- Restricts ingestion to selected top-level folders.
- Reads `.md` files as UTF-8.
- Computes a timestamp per file (best-effort creation time fallback).
- Sends each note to Hindsight via `client.retain(...)`.
- Shows progress and per-file status in the terminal.

## Current Default Configuration

These values come from `main.py`:

- `VAULT_PATH = C:/Users/jonfl/Amicus`
- `INCLUDE_FOLDERS = {"01-Projects", "02-Areas", "03-Resources"}`
- `BANK_ID = "amicus-2026"`
- `Hindsight base_url = "http://localhost:8888"`

Update them before running if your environment differs.

## Requirements

- Python 3.14+ (per `pyproject.toml`)
- A running Hindsight server (default expected at `http://localhost:8888`)
- A valid Hindsight bank ID that exists on the server

## Install

From the project root:

```bash
uv venv
.venv\Scripts\activate.bat
uv pip install -r requirements.txt
```

## Usage

Run:

```bash
uv run main.py
```

You will see:

- A progress bar (`Ingesting notes`)
- A success line per note, for example: `[01-Projects] Note Name.md`
- Error lines for files that fail to ingest

## Configure the Script

Open `main.py` and adjust:

```python
VAULT_PATH = Path(r"C:/path/to/your/vault").resolve()
INCLUDE_FOLDERS = {"01-Projects", "02-Areas", "03-Resources"}
BANK_ID = "your-bank-id"

client = Hindsight(base_url="http://localhost:8888")
```

## Creating a Bank (Optional)

`main.py` includes a commented example:

```python
# client.create_bank(
#     bank_id="test",
#     name="Test Bank",
#     mission="You are an Obsidian Vault Manager",
#     disposition={
#         "skepticism": 2,
#         "literalism": 4,
#         "empathy": 5
#     })
```

If your target bank does not exist, create one first (either by uncommenting/adapting this or via your Hindsight API workflow).

## Notes on Timestamps

`get_creation_time(...)` uses:

- `st_birthtime` when available
- `st_mtime` fallback otherwise

On many Linux filesystems, true creation time is not available, so modified time is used.

## Troubleshooting

- `Vault path not found`: verify `VAULT_PATH` in `main.py`.
- Connection issues to Hindsight: verify `base_url` and that the server is running.
- Ingest errors for individual files: check file encoding/content and inspect the printed exception.

## Safety Tips

- Start with a small test folder to validate mapping and metadata.
- Use a dedicated test bank before ingesting your full vault.

