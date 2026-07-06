from pathlib import Path

from tools.report import build_report, frames_to_dataframe, load_dataframe

ROOT = Path(__file__).resolve().parent.parent
CAN_LOG = ROOT / "samples" / "drive_cycle_can.log"
CSV_LOG = ROOT / "samples" / "drive_cycle_log.csv"


def test_can_log_decodes_into_signal_columns():
    df = frames_to_dataframe(CAN_LOG)
    assert not df.empty
    for column in ["time_s", "pack_current_a", "min_cell_voltage_v", "max_cell_voltage_v"]:
        assert column in df.columns
    # the drive cycle ramps a cell past the 4.25 V over-voltage limit
    assert df["max_cell_voltage_v"].max() >= 4.25


def test_load_dataframe_dispatches_on_suffix():
    # the CSV carries temperature, the CAN log does not
    assert "max_cell_temp_c" in load_dataframe(CSV_LOG).columns
    assert "max_cell_temp_c" not in load_dataframe(CAN_LOG).columns


def test_report_from_can_log_flags_violations(tmp_path):
    out = tmp_path / "can_report.html"
    build_report(CAN_LOG, out)
    html = out.read_text()
    assert "Limit violations" in html
    assert "over-voltage" in html  # the ramp trips OVP on the bus signals
