from datetime import datetime
from pathlib import Path

from jinja2 import Template

from drift import GOLDEN_DIR, compare

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"

TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Config drift report</title>
<style>
  body { font-family: Segoe UI, Arial, sans-serif; margin: 2rem; background: #f5f6f8; color: #222; }
  .meta { color: #666; margin-bottom: 1.5rem; }
  .card { background: #fff; border-radius: 8px; padding: 1rem 1.5rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,.15); }
  .ok { color: #1a7f37; }
  .drift { color: #cf222e; }
  code { display: block; padding: 2px 6px; font-family: Consolas, monospace; }
  .added { background: #e6ffec; }
  .removed { background: #ffebe9; }
</style>
</head>
<body>
<h1>Config drift report</h1>
<div class="meta">Generated on {{ generated }}</div>
{% for d in devices %}
<div class="card">
  <h2>{{ d.name }}
    {% if d.drift %}<span class="drift">DRIFT</span>{% else %}<span class="ok">OK</span>{% endif %}
  </h2>
  {% if d.drift %}
    <p>{{ d.removed|length }} line(s) removed, {{ d.added|length }} line(s) added compared to the golden config.</p>
    {% for l in d.removed %}<code class="removed">- {{ l }}</code>{% endfor %}
    {% for l in d.added %}<code class="added">+ {{ l }}</code>{% endfor %}
  {% else %}
    <p>The running config matches the golden config.</p>
  {% endif %}
</div>
{% endfor %}
</body>
</html>""", autoescape=True)


def build_devices():
    devices = []
    for golden_file in sorted(GOLDEN_DIR.glob("*.cfg")):
        name = golden_file.stem
        added, removed = compare(name)
        devices.append({
            "name": name,
            "added": added,
            "removed": removed,
            "drift": bool(added or removed),
        })
    return devices


def main():
    REPORT_DIR.mkdir(exist_ok=True)
    html = TEMPLATE.render(
        generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        devices=build_devices(),
    )
    path = REPORT_DIR / "drift_report.html"
    path.write_text(html, encoding="utf-8")
    print(f"[+] Report written to {path}")
    return path


if __name__ == "__main__":
    main()