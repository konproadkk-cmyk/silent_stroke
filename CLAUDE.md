# Silent Stroke

Combines firmware (ESP32-based sensor boards) and a desktop UI for collecting
physiological sensor data (ECG, PPG) for stroke-related research.

## Repo layout

- `oil_firmware/` — PlatformIO firmware project(s) for the "oil" board.
  - `test_components/` — Seeed XIAO ESP32-C3 sketch that reads an AD8232 ECG
    module and a MAX30102 pulse oximeter, and streams CSV over serial at
    115200 baud: `ad8232_raw,leads_off,max_ir,max_red` (~50 Hz, header line
    printed once at boot).
- `proad_firmware/` — separate firmware project (not yet reviewed in detail).
- `oil_desktop_app/` — PyQt6 desktop app that connects to `oil_firmware`'s
  serial output, plots ECG/IR/Red in real time (pyqtgraph, 3 stacked plots),
  and logs readings to CSV via a Start/Stop recording button.
  - Run with: `conda activate stroke-collect-data && pip install -r requirements.txt && python main.py`
  - See `oil_desktop_app/README.md` for details.

## Environment

- Desktop app testing uses the conda env **`stroke-collect-data`** (not a
  venv) — always activate this env for running/testing `oil_desktop_app`.

## Session log

- 2026-07-09: Built `oil_desktop_app` (PyQt6 + pyqtgraph) to visualize and
  record `oil_firmware/test_components` sensor output in real time. Verified
  headless (parser, CSV recording, window construction) in the
  `stroke-collect-data` conda env; not yet tested against real hardware.

## Next session

- **Build ESP32 firmware** — next task is firmware work on the ESP32 side
  (scope not yet defined as of 2026-07-09; clarify with user at start of
  next session whether this extends `oil_firmware`, `proad_firmware`, or is
  a new board/project).
