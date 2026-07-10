# Oil Sensor Monitor (Desktop)

PyQt6 desktop app for the `oil_firmware/test_components` sketch (AD8232 ECG +
MAX30102 pulse oximeter on a Seeed XIAO ESP32-C3). Reads the serial CSV
stream, plots ECG/IR/Red in real time, and can record readings to a CSV file.

## Setup

```bash
conda activate stroke-collect-data
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

1. Flash and connect the board (see `oil_firmware/test_components`).
2. Pick its serial port from the dropdown (use Refresh if it's not listed) and click **Connect**.
3. Click **Start Recording** to choose a CSV file and begin logging; **Stop Recording** to close it.

## Output CSV columns

`timestamp, ad8232_raw, leads_off, max_ir, max_red`
