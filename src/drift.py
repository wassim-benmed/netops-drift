import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GOLDEN_DIR = BASE_DIR / "configs" / "golden"
BACKUP_DIR = BASE_DIR / "configs" / "backups"


def read_lines(path):
    return path.read_text(encoding="utf-8").splitlines()


def compare(name):
    golden = read_lines(GOLDEN_DIR / f"{name}.cfg")
    current = read_lines(BACKUP_DIR / f"{name}.cfg")
    golden_set, current_set = set(golden), set(current)
    added = [line for line in current if line not in golden_set]
    removed = [line for line in golden if line not in current_set]
    return added, removed


def main():
    drift_found = False
    for golden_file in sorted(GOLDEN_DIR.glob("*.cfg")):
        name = golden_file.stem
        if not (BACKUP_DIR / golden_file.name).exists():
            print(f"[!] {name}: no backup found, run collector.py first")
            drift_found = True
            continue
        added, removed = compare(name)
        if not added and not removed:
            print(f"[OK] {name}: no drift")
            continue
        drift_found = True
        print(f"[DRIFT] {name}: {len(added)} added, {len(removed)} removed")
        for line in removed:
            print(f"  - {line}")
        for line in added:
            print(f"  + {line}")
    return 1 if drift_found else 0


if __name__ == "__main__":
    sys.exit(main())