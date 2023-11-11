import serial
import struct
import time
import random

# 串口参数
port = "/dev/tnt1"
baud_rate = 115200

# 发送数据
with serial.Serial(port, baud_rate, timeout=1) as ser:
    loop_count = 0
    while True:
        params = [random.randint(0, 100) for _ in range(60)]
        length = len(params) * 4 + 8 + 4
        msg_type = 1
        status = 2
        loop_count = (loop_count + 1) & 0xff
        utime = time.time()

        sum = length + msg_type + status + loop_count
        for value in params:
            for byte in struct.pack("<f", value):
                sum += byte
        for byte in struct.pack("<d", utime):
            sum += byte

        frame = b"\xeb\x90"
        frame += struct.pack("<H", length) 
        frame += struct.pack("<d", utime) 
        for value in params:
            frame += struct.pack("<f", value) 
        frame += struct.pack("<B", msg_type)
        frame += struct.pack("<B", status)
        frame += struct.pack("<B", loop_count)
        frame += struct.pack("<B", sum & 0xFF)
        print("length={},checksum={}".format(length, sum&0xff))
        ser.write(frame)
        time.sleep(0.01)
