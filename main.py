# -*- coding: utf-8 -*-
import sys
import struct
import os
import csv
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
    QFileDialog,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal, QThread

PARAMS_ROWS = 6
PARAMS_COLS = 10
BAUD_RATE = 115200
PARAMS_NAME = [
    '测试', 'Param2', 'Param3', 'Param4', 'Param5', 'Param6', 'Param7', 'Param8', 'Param9', 'Param10',
    'Param11', 'Param12', 'Param13', 'Param14', 'Param15', 'Param16', 'Param17', 'Param18', 'Param19', 'Param20',
    'Param21', 'Param22', 'Param23', 'Param24', 'Param25', 'Param26', 'Param27', 'Param28', 'Param29', 'Param30',
    'Param31', 'Param32', 'Param33', 'Param34', 'Param35', 'Param36', 'Param37', 'Param38', 'Param39', 'Param40',
    'Param41', 'Param42', 'Param43', 'Param44', 'Param45', 'Param46', 'Param47', 'Param48', 'Param49', 'Param50',
    'Param51', 'Param52', 'Param53', 'Param54', 'Param55', 'Param56', 'Param57', 'Param58', 'Param59', 'Param60'
]

class SerialData:
    def __init__(self, utime, params, msg_type, status, loop_count):
        self.utime = utime
        self.params = params
        self.msg_type = msg_type
        self.status = status
        self.loop_count = loop_count


class SerialReaderThread(QThread):
    data_received = pyqtSignal(SerialData)
    checksum_error = pyqtSignal()
    frame_header_error = pyqtSignal()

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.is_running = True

    def run(self):
        while self.is_running:
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
                        print("length={},checksum={},expect={}".format(length, sum&0xff, checksum))
                        self.checksum_error.emit()
                else:
                    self.frame_header_error.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Serial Port Reader")

        self.serial_port_combobox = QComboBox(self)
        self.populate_serial_ports()

        self.open_serial_port_button = QPushButton("打开串口", self)
        self.open_serial_port_button.clicked.connect(self.open_serial_port)

        self.select_file_button = QPushButton("选择文件", self)
        self.select_file_button.clicked.connect(self.select_file)

        hbox = QHBoxLayout()
        hbox.addWidget(self.serial_port_combobox)
        hbox.addWidget(self.open_serial_port_button)
        hbox.addWidget(self.select_file_button)

        self.csv_file_name = None

        layout = QGridLayout()
        self.labels = [
            [PARAMS_NAME[row * PARAMS_COLS + col] for col in range(PARAMS_COLS)]
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

    def select_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "选择保存文件", "",
                    "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            # Ensure that the file has a .csv extension
            if not file_name.endswith('.csv'):
                file_name += '.csv'

            if os.access(os.path.dirname(file_name), os.W_OK):
                with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    # Create and write data to CSV
                    row_data = [
                        "utime", "msg_type", "status", "loop_count", "params", *PARAMS_NAME
                    ]
                    csvwriter.writerow(row_data)

                    self.csv_file_name = file_name
                    self.status_bar.showMessage(f"文件将保存到: {file_name}")
            else:
                self.status_bar.showMessage(f"文件无法保存到: {file_name}")

    def populate_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        self.serial_port_combobox.clear()
        for port in ports:
            self.serial_port_combobox.addItem(port.device)
        # self.serial_port_combobox.addItem('/dev/tnt0')

    def open_serial_port(self):
        if self.serial_port is not None and self.serial_port.is_open:
            self.serial_reader_thread.is_running = False
            self.serial_reader_thread.wait()
            self.serial_port.close()
            self.open_serial_port_button.setText("打开串口")
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
            self.open_serial_port_button.setText("关闭串口")
        except serial.SerialException as e:
            print(e)

    def update_line_edits(self, data: SerialData):
        self.status_bar.showMessage("收到数据")
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

        if hasattr(self, 'csv_file_name') and self.csv_file_name is not None and os.access(os.path.dirname(self.csv_file_name), os.W_OK):
            with open(self.csv_file_name, 'a', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                # Create and write data to CSV
                row_data = [
                    data.utime, data.msg_type, data.status, data.loop_count, *data.params
                ]
                csvwriter.writerow(row_data)

    def show_checksum_error(self):
        self.status_bar.showMessage("校验错误")

    def show_frame_header_error(self):
        self.status_bar.showMessage("未发现帧头")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
