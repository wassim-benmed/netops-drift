import sys

from core import check_all
from report import main as build_report


def main():
    problems = 0
    for r in check_all():
        name = r["name"]
        if r["status"] == "ERROR":
            print(f"[ERROR] {name}: {r['error']}")
            problems += 1
        elif r["status"] == "NO_GOLDEN":
            print(f"[!] {name}: no golden config, comparison skipped")
        elif r["status"] == "DRIFT":
            print(f"[DRIFT] {name}: {len(r['added'])} added, {len(r['removed'])} removed")
            problems += 1
        else:
            print(f"[OK] {name}: no drift")

    try:
        build_report()
    except FileNotFoundError as e:
        print(f"[!] Report not generated: {e}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())