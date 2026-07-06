"""Generate an HTML report from a signal log.

The input can be either a CSV of per-second pack measurements, or a candump-format
CAN log of the frames defined in ``can/bms.dbc``. Either way the tool checks every
sample against the protection limits and writes a small standalone HTML report.
This is my stand-in for the report generators a real bench tool produces (ECU-TEST
calls them ATX reports), and reading a bus log is closer to what a bench actually
does after a test run.

Usage:
    python tools/report.py samples/drive_cycle_log.csv -o report.html
    python tools/report.py samples/drive_cycle_can.log -o report.html
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from jinja2 import Template

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bms.protection import Limits  # noqa: E402

DBC_PATH = Path(__file__).resolve().parent.parent / "can" / "bms.dbc"

# Signals the report knows how to summarise and limit-check. A CAN log only
# carries a subset (no temperature on the bus in this project), so anything
# missing from the input is simply skipped.
ALL_SIGNALS = ["pack_current_a", "min_cell_voltage_v", "max_cell_voltage_v", "max_cell_temp_c"]

# DBC signal name -> report column name, for the analog signals in PackStatus.
CAN_SIGNAL_COLUMNS = {
    "PackCurrent_A": "pack_current_a",
    "MinCellVoltage_V": "min_cell_voltage_v",
    "MaxCellVoltage_V": "max_cell_voltage_v",
}

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


def frames_to_dataframe(log_path):
    """Read a candump CAN log, decode the PackStatus frames with the DBC, and
    return a dataframe shaped like the CSV the report already understands."""
    from can import CanutilsLogReader
    import cantools

    db = cantools.database.load_file(DBC_PATH)
    pack_status = db.get_message_by_name("PackStatus")
    rows = []
    start = None
    for frame in CanutilsLogReader(str(log_path)):
        if frame.arbitration_id != pack_status.frame_id:
            continue  # only PackStatus carries the analog signals we report on
        if start is None:
            start = frame.timestamp
        decoded = db.decode_message(frame.arbitration_id, frame.data)
        row = {"time_s": round(frame.timestamp - start)}
        for signal, column in CAN_SIGNAL_COLUMNS.items():
            row[column] = float(decoded[signal])
        rows.append(row)
    return pd.DataFrame(rows)


def load_dataframe(source_path):
    """Load either a CSV of samples or a candump .log, chosen by file suffix."""
    source_path = Path(source_path)
    if source_path.suffix == ".log":
        return frames_to_dataframe(source_path)
    return pd.read_csv(source_path)


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
            if column not in df.columns:
                continue  # signal not present in this log (e.g. temperature on a CAN log)
            value = row[column]
            if trips(value):
                violations.append({
                    "time": row["time_s"], "check": name,
                    "value": value, "limit": limit,
                })
    return violations


def build_report(source_path, output_path):
    df = load_dataframe(source_path)
    limits = Limits()
    summary = [
        {"name": s, "min": df[s].min(), "max": df[s].max()}
        for s in ALL_SIGNALS if s in df.columns
    ]
    duration = int(df["time_s"].max() - df["time_s"].min()) if not df.empty else 0
    html = TEMPLATE.render(
        source=source_path,
        rows=len(df),
        duration=duration,
        summary=summary,
        violations=find_violations(df, limits),
    )
    Path(output_path).write_text(html)
    print(f"wrote {output_path} ({len(df)} samples)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="signal log: a .csv of samples or a candump .log of CAN frames")
    parser.add_argument("-o", "--output", default="report.html")
    args = parser.parse_args()
    build_report(args.source, args.output)
