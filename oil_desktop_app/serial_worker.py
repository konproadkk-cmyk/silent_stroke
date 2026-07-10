"""Background serial reader for the oil_firmware test_components sketch.

Expects CSV lines of the form: ad8232_raw,leads_off,max_ir,max_red
(the firmware also prints a header line and boot log lines, which are
silently skipped since they don't parse as 4 numbers).
"""
import time

import serial
from PyQt6.QtCore import QThread, pyqtSignal
from serial.tools import list_ports

BAUD_RATE = 115200


def list_serial_ports() -> list[str]:
    return [p.device for p in list_ports.comports()]


class SerialWorker(QThread):
    sample_received = pyqtSignal(float, int, int, int, int)  # t, ad8232_raw, leads_off, ir, red
    connection_error = pyqtSignal(str)
    connected = pyqtSignal()
    disconnected = pyqtSignal()

    def __init__(self, port: str, baud_rate: int = BAUD_RATE, parent=None):
        super().__init__(parent)
        self._port = port
        self._baud_rate = baud_rate
        self._running = False

    def run(self):
        try:
            ser = serial.Serial(self._port, self._baud_rate, timeout=1)
        except serial.SerialException as exc:
            self.connection_error.emit(str(exc))
            return

        self._running = True
        self.connected.emit()
        start_time = time.monotonic()

        try:
            while self._running:
                raw_line = ser.readline()
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8", errors="ignore").strip()
                parsed = self._parse_line(line)
                if parsed is None:
                    continue
                ad8232_raw, leads_off, ir_value, red_value = parsed
                elapsed = time.monotonic() - start_time
                self.sample_received.emit(elapsed, ad8232_raw, leads_off, ir_value, red_value)
        except serial.SerialException as exc:
            self.connection_error.emit(str(exc))
        finally:
            ser.close()
            self.disconnected.emit()

    @staticmethod
    def _parse_line(line: str):
        fields = line.split(",")
        if len(fields) != 4:
            return None
        try:
            return tuple(int(f) for f in fields)
        except ValueError:
            return None

    def stop(self):
        self._running = False
        self.wait(2000)
