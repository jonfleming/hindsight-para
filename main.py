import os
from pathlib import Path
from datetime import datetime, timezone
from tqdm import tqdm
import json

# --- CONFIG ---
VAULT_PATH = Path(r"C:/Users/jonfl/Amicus").resolve()
INCLUDE_FOLDERS = {"01-Projects", "02-Areas", "03-Resources"}
BANK_ID ="amicus-2026"

# --- TRACKING CONFIG ---
TRACKING_FILE = Path("ingestion_tracking.json")

# --- HINDSIGHT CLIENT SETUP ---
# Replace with your actual import/init
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")
# client.create_bank(
#     bank_id="test", 
#     name="Test Bank", 
#     mission="You are an Obsidian Vault Manager",
#     disposition={
#         "skepticism": 2,
#         "literalism": 4,
#         "empathy": 5
#     })

def get_creation_time(path: Path) -> str:
    """
    Cross-platform creation time.
    Falls back to last modified time if needed.
    Returns ISO 8601 string.
    """
    stat = path.stat()

    if hasattr(stat, "st_birthtime"):  # macOS
        ts = stat.st_birthtime
    else:
        # Linux typically doesn't have creation time
        ts = stat.st_mtime

    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def get_last_run_time():
    """Get the timestamp of the last successful run."""
    if TRACKING_FILE.exists():
        try:
            with open(TRACKING_FILE, 'r') as f:
                data = json.load(f)
                return datetime.fromisoformat(data.get('last_run', '2020-01-01T00:00:00+00:00'))
        except (json.JSONDecodeError, KeyError):
            return datetime.min.replace(tzinfo=timezone.utc)
    return datetime.min.replace(tzinfo=timezone.utc)


def set_last_run_time():
    """Save the current timestamp as the last run time."""
    data = {
        'last_run': datetime.now(timezone.utc).isoformat()
    }
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def is_new_file(file_path: Path, last_run_time: datetime) -> bool:
    """Check if a file should be considered new (created or modified after last run)."""
    stat = file_path.stat()
    
    # Use creation time if available, otherwise modified time
    file_time = stat.st_birthtime if hasattr(stat, "st_birthtime") else stat.st_mtime
    file_datetime = datetime.fromtimestamp(file_time, tz=timezone.utc)
    
    return file_datetime > last_run_time


def collect_markdown_files():
    files = []

    if not VAULT_PATH.exists():
        raise FileNotFoundError(f"Vault path not found: {VAULT_PATH}")

    for root, dirs, filenames in os.walk(str(VAULT_PATH)):
        root_path = Path(root)

        # Determine top-level folder (Projects, Areas, etc.)
        try:
            relative = root_path.relative_to(VAULT_PATH)
        except ValueError:
            continue

        # At vault root, only descend into folders we care about.
        if not relative.parts:
            dirs[:] = [d for d in dirs if d in INCLUDE_FOLDERS]
            continue

        top_level = relative.parts[0]

        if top_level not in INCLUDE_FOLDERS:
            continue

        for f in filenames:
            if f.endswith(".md"):
                files.append(root_path / f)

    return files


def ingest():
    last_run_time = get_last_run_time()
    files = collect_markdown_files()
    
    # Filter for new files only
    new_files = []
    skipped_files = []
    for file_path in files:
        if is_new_file(file_path, last_run_time):
            new_files.append(file_path)
        else:
            skipped_files.append(file_path)
    
    tqdm.write(f"Found {len(new_files)} new files to ingest, {len(skipped_files)} files to skip")
    if last_run_time != datetime.min.replace(tzinfo=timezone.utc):
        tqdm.write(f"Last run: {last_run_time.isoformat()}")

    if not new_files:
        tqdm.write("No new files to ingest.")
        return

    for file_path in tqdm(new_files, desc="Ingesting new notes"):
        try:
            content = file_path.read_text(encoding="utf-8")

            # context = top-level folder
            relative = file_path.relative_to(VAULT_PATH)
            context = relative.parts[0]

            timestamp = get_creation_time(file_path)

            client.retain(
                bank_id=BANK_ID,
                content=content,
                context=context,
                timestamp=timestamp,
                document_id=str(file_path)
            )

            tqdm.write(f"[{context}] {file_path.name}")

        except Exception as e:
            tqdm.write(f"ERROR: {file_path} -> {e}")
    
    # Update tracking file
    set_last_run_time()
    tqdm.write(f"Updated tracking file. Last run: {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    ingest()