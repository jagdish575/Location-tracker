# show_logs.py
import json
from pathlib import Path

# Path to your log file
LOGFILE = Path(__file__).resolve().parent / "locations_log.jsonl"

def show_logs():
    print(f"📜 Reading log file: {LOGFILE}")
    if not LOGFILE.is_file():
        print("🚨 Log file not found!")
        return

    # Check file size
    print(f"📏 File size: {LOGFILE.stat().st_size} bytes")

    # Read and parse each line
    records = []
    with open(LOGFILE, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except Exception as e:
                print(f"❌ JSON error on line {i}: {e}")
                print("🔸 Raw line:", line)

    print(f"✅ Total records parsed: {len(records)}")
    if records:
        print("\n📝 First 3 records:")
        for r in records[:3]:
            print(json.dumps(r, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    show_logs()
