import csv
import datetime as dt
from collections import deque

import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from serial_worker import SerialWorker, list_serial_ports

BUFFER_SECONDS = 10
SAMPLE_RATE_HZ = 50
BUFFER_LEN = BUFFER_SECONDS * SAMPLE_RATE_HZ


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Oil Sensor Monitor")
        self.resize(1000, 700)

        self.worker: SerialWorker | None = None
        self.csv_writer = None
        self.csv_file = None

        self.t_buf = deque(maxlen=BUFFER_LEN)
        self.ecg_buf = deque(maxlen=BUFFER_LEN)
        self.ir_buf = deque(maxlen=BUFFER_LEN)
        self.red_buf = deque(maxlen=BUFFER_LEN)

        self._build_ui()
        self._refresh_ports()

    # ---------------------------------------------------------------- UI --
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        controls = QHBoxLayout()
        root.addLayout(controls)

        controls.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        controls.addWidget(self.port_combo)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_ports)
        controls.addWidget(self.refresh_btn)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._toggle_connection)
        controls.addWidget(self.connect_btn)

        self.record_btn = QPushButton("Start Recording")
        self.record_btn.setEnabled(False)
        self.record_btn.clicked.connect(self._toggle_recording)
        controls.addWidget(self.record_btn)

        controls.addStretch()

        self.status_label = QLabel("Disconnected")
        controls.addWidget(self.status_label)

        pg.setConfigOptions(antialias=True)

        self.ecg_plot = pg.PlotWidget(title="ECG (AD8232 raw)")
        self.ir_plot = pg.PlotWidget(title="PPG - IR (MAX30102)")
        self.red_plot = pg.PlotWidget(title="PPG - Red (MAX30102)")
        for plot in (self.ecg_plot, self.ir_plot, self.red_plot):
            plot.setLabel("bottom", "Time", "s")
            plot.showGrid(x=True, y=True, alpha=0.3)
            root.addWidget(plot)

        self.ecg_curve = self.ecg_plot.plot(pen=pg.mkPen("c", width=1))
        self.ir_curve = self.ir_plot.plot(pen=pg.mkPen("y", width=1))
        self.red_curve = self.red_plot.plot(pen=pg.mkPen("r", width=1))

    # ------------------------------------------------------------ Serial --
    def _refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        ports = list_serial_ports()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)

    def _toggle_connection(self):
        if self.worker is not None:
            self._disconnect()
            return

        port = self.port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "No port selected", "Select a serial port first.")
            return

        self.worker = SerialWorker(port)
        self.worker.sample_received.connect(self._on_sample)
        self.worker.connected.connect(self._on_connected)
        self.worker.disconnected.connect(self._on_disconnected)
        self.worker.connection_error.connect(self._on_connection_error)
        self.worker.start()
        self.connect_btn.setEnabled(False)

    def _disconnect(self):
        if self.worker is not None:
            self.worker.stop()
        if self.csv_file is not None:
            self._stop_recording()

    def _on_connected(self):
        self.connect_btn.setText("Disconnect")
        self.connect_btn.setEnabled(True)
        self.record_btn.setEnabled(True)
        self.status_label.setText(f"Connected to {self.port_combo.currentText()}")

    def _on_disconnected(self):
        self.worker = None
        self.connect_btn.setText("Connect")
        self.connect_btn.setEnabled(True)
        self.record_btn.setEnabled(False)
        self.status_label.setText("Disconnected")
        if self.csv_file is not None:
            self._stop_recording()

    def _on_connection_error(self, message: str):
        QMessageBox.critical(self, "Serial error", message)
        self.connect_btn.setEnabled(True)

    # ------------------------------------------------------------- Data --
    def _on_sample(self, t, ad8232_raw, leads_off, ir_value, red_value):
        self.t_buf.append(t)
        self.ecg_buf.append(ad8232_raw)
        self.ir_buf.append(ir_value)
        self.red_buf.append(red_value)

        self.ecg_curve.setData(self.t_buf, self.ecg_buf)
        self.ir_curve.setData(self.t_buf, self.ir_buf)
        self.red_curve.setData(self.t_buf, self.red_buf)

        leads_off_text = " | LEADS OFF" if leads_off else ""
        self.status_label.setText(f"Connected to {self.port_combo.currentText()}{leads_off_text}")

        if self.csv_writer is not None:
            self.csv_writer.writerow(
                [dt.datetime.now().isoformat(timespec="milliseconds"), ad8232_raw, leads_off, ir_value, red_value]
            )

    # --------------------------------------------------------- Recording --
    def _toggle_recording(self):
        if self.csv_file is None:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        default_name = f"readings_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Save recording as", default_name, "CSV files (*.csv)")
        if not path:
            return

        self.csv_file = open(path, "w", newline="")
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["timestamp", "ad8232_raw", "leads_off", "max_ir", "max_red"])
        self.record_btn.setText("Stop Recording")

    def _stop_recording(self):
        if self.csv_file is not None:
            self.csv_file.close()
        self.csv_file = None
        self.csv_writer = None
        self.record_btn.setText("Start Recording")

    def closeEvent(self, event):
        self._disconnect()
        super().closeEvent(event)
