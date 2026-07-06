"""Generate an HTML report from a signal log CSV.

Reads a log with per-second pack measurements, checks every row against the
protection limits, and writes a small standalone HTML report. This is my
stand-in for the report generators a real bench tool produces (ECU-TEST
calls them ATX reports).

Usage:
    python tools/report.py samples/drive_cycle_log.csv -o report.html
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from jinja2 import Template

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bms.protection import Limits  # noqa: E402

TEMPLATE = Template("""\
<!doctype html>
<html>
<head><meta charset="utf-8"><title>BMS log report</title>
<style>
 body { font-family: sans-serif; margin: 2em; color: #222; }
 table { border-collapse: collapse; margin-top: 1em; }
 td, th { border: 1px solid #999; padding: 4px 10px; text-align: right; }
 th { background: #eee; }
 .bad { color: #b00020; font-weight: bold; }
</style></head>
<body>
<h1>BMS log report</h1>
<p>Source: {{ source }} — {{ rows }} samples, {{ duration }} s</p>
<h2>Summary</h2>
<table>
 <tr><th>Signal</th><th>Min</th><th>Max</th></tr>
 {% for row in summary %}
 <tr><td style="text-align:left">{{ row.name }}</td><td>{{ row.min }}</td><td>{{ row.max }}</td></tr>
 {% endfor %}
</table>
<h2>Limit violations</h2>
{% if violations %}
<table>
 <tr><th>t (s)</th><th>Check</th><th>Value</th><th>Limit</th></tr>
 {% for v in violations %}
 <tr class="bad"><td>{{ v.time }}</td><td style="text-align:left">{{ v.check }}</td><td>{{ v.value }}</td><td>{{ v.limit }}</td></tr>
 {% endfor %}
</table>
{% else %}
<p>None. All samples inside limits.</p>
{% endif %}
</body>
</html>
""")


def find_violations(df, limits):
    violations = []
    checks = [
        ("cell over-voltage", "max_cell_voltage_v",
         lambda v: v >= limits.cell_over_voltage_v, limits.cell_over_voltage_v),
        ("cell under-voltage", "min_cell_voltage_v",
         lambda v: v <= limits.cell_under_voltage_v, limits.cell_under_voltage_v),
        ("over-temperature", "max_cell_temp_c",
         lambda v: v >= limits.over_temperature_c, limits.over_temperature_c),
        ("over-current", "pack_current_a",
         lambda v: abs(v) >= limits.over_current_a, limits.over_current_a),
    ]
    for _, row in df.iterrows():
        for name, column, trips, limit in checks:
            value = row[column]
            if trips(value):
                violations.append({
                    "time": row["time_s"], "check": name,
                    "value": value, "limit": limit,
                })
    return violations


def build_report(csv_path, output_path):
    df = pd.read_csv(csv_path)
    limits = Limits()
    signals = ["pack_current_a", "min_cell_voltage_v", "max_cell_voltage_v", "max_cell_temp_c"]
    summary = [
        {"name": s, "min": df[s].min(), "max": df[s].max()} for s in signals
    ]
    html = TEMPLATE.render(
        source=csv_path,
        rows=len(df),
        duration=int(df["time_s"].max() - df["time_s"].min()),
        summary=summary,
        violations=find_violations(df, limits),
    )
    Path(output_path).write_text(html)
    print(f"wrote {output_path} ({len(df)} samples)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", help="signal log csv")
    parser.add_argument("-o", "--output", default="report.html")
    args = parser.parse_args()
    build_report(args.csv, args.output)
