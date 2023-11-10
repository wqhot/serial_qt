import sys
import threading
import struct
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QComboBox,
    QPushButton,
    QGridLayout,
    QLineEdit,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QStatusBar,
)
from PyQt5.QtCore import Qt, pyqtSignal

PARAMS_ROWS = 6
PARAMS_COLS = 10
BAUD_RATE = 115200


class SerialData:
    def __init__(self, utime, params, msg_type, status, loop_count):
        self.utime = utime
        self.params = params
        self.msg_type = msg_type
        self.status = status
        self.loop_count = loop_count


class SerialReaderThread(threading.Thread):
    data_received = pyqtSignal(SerialData)
    checksum_error = pyqtSignal()
    frame_header_error = pyqtSignal()

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.is_running = True

    def run(self):
        while self.running:
            if self.serial_port.read() == b"\xeb":
                if self.serial_port.read() == b"\x90":
                    length = struct.unpack("<H", self.serial_port.read(2))[0]
                    utime = struct.unpack("<d", self.serial_port.read(8))[0]
                    params = [0.0] * (length // 4 - 3)
                    for i in range(length // 4 - 3):
                        params[i] = struct.unpack("<f", self.serial_port.read(4))[0]

                    msg_type = struct.unpack("<B", self.serial_port.read(1))[0]
                    status = struct.unpack("<B", self.serial_port.read(1))[0]
                    loop_count = struct.unpack("<B", self.serial_port.read(1))[0]
                    checksum = struct.unpack("<B", self.serial_port.read(1))[0]

                    sum = length + msg_type + status + loop_count
                    for value in params:
                        for byte in struct.pack("<f", value):
                            sum += byte

                    for byte in struct.pack("<d", utime):
                        sum += byte

                    if sum & 0xFF == checksum:
                        data = SerialData(utime, params, msg_type, status, loop_count)
                        self.data_received.emit(data)
                    else:
                        self.checksum_error.emit()
                else:
                    self.frame_header_error.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Serial Port Reader")

        self.serial_port_combobox = QComboBox(self)
        self.populate_serial_ports()

        self.open_serial_port_button = QPushButton("Open Serial Port", self)
        self.open_serial_port_button.clicked.connect(self.open_serial_port)

        hbox = QHBoxLayout()
        hbox.addWidget(self.serial_port_combobox)
        hbox.addWidget(self.open_serial_port_button)

        layout = QGridLayout()
        self.labels = [
            ["Param{}".format(row * PARAMS_COLS + col) for col in range(PARAMS_COLS)]
            for row in range(PARAMS_ROWS)
        ]
        self.line_edits = [
            ["".format(row, col) for col in range(PARAMS_COLS)]
            for row in range(PARAMS_ROWS)
        ]
        self.line_edit_widgets = []
        for row in range(PARAMS_ROWS):
            for col in range(PARAMS_COLS):
                label = QLabel(self.labels[row][col])
                label.setAlignment(Qt.AlignCenter)
                line_edit = QLineEdit(self.line_edits[row][col])
                line_edit.setAlignment(Qt.AlignCenter)
                self.line_edit_widgets.append(line_edit)
                layout.addWidget(label, row * 2, col)
                layout.addWidget(line_edit, row * 2 + 1, col)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(layout)
        widget = QWidget()
        widget.setLayout(vbox)
        self.setCentralWidget(widget)

        self.serial_port = None
        self.serial_reader_thread = None

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.show()

    def populate_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        self.serial_port_combobox.clear()
        for port in ports:
            self.serial_port_combobox.addItem(port.device)

    def open_serial_port(self):
        if self.serial_port is not None and self.serial_port.is_open:
            self.serial_reader_thread.is_running = False
            self.serial_reader_thread.join()
            self.serial_port.close()
            self.open_serial_port_button.setText("Open Serial Port")
            return

        port_name = self.serial_port_combobox.currentText()
        try:
            self.serial_port = serial.Serial(port_name, BAUD_RATE, timeout=1)
            self.serial_reader_thread = SerialReaderThread(self.serial_port)
            self.serial_reader_thread.data_received.connect(self.update_line_edits)
            self.serial_reader_thread.checksum_error.connect(self.show_checksum_error)
            self.serial_reader_thread.frame_header_error.connect(
                self.show_frame_header_error
            )
            self.serial_reader_thread.start()
            self.open_serial_port_button.setText("Close Serial Port")
        except serial.SerialException as e:
            print(e)

    def update_line_edits(self, data: SerialData):
        for i, value in enumerate(data.params):
            if i >= len(self.line_edit_widgets):
                return
            self.line_edit_widgets[i].setText(str(value))
        if len(data.params) + 4 > len(data.params):
            return
        self.line_edit_widgets[0 + len(data.params)].setText(str(data.utime))
        self.line_edit_widgets[1 + len(data.params)].setText(str(data.msg_type))
        self.line_edit_widgets[2 + len(data.params)].setText(str(data.status))
        self.line_edit_widgets[3 + len(data.params)].setText(str(data.loop_count))
        self.status_bar.showMessage("Data received!")

    def show_checksum_error(self):
        self.status_bar.showMessage("Checksum error!")

    def show_frame_header_error(self):
        self.status_bar.showMessage("Frame header not found!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
