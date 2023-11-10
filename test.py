import serial
import struct
import time

# 串口参数
port = "COM3"
baud_rate = 115200

# 发送数据
with serial.Serial(port, baud_rate, timeout=1) as ser:
    loop_count = 0
    while True:
        params = [i + 1 for i in range(60)]
        length = len(params) * 4 + 8 + 4
        msg_type = 1
        status = 2
        loop_count = loop_count + 1

        # 计算校验和
        sum = length + msg_type + status + loop_count
        for value in params:
            for byte in struct.pack("<f", value):
                sum += byte

        # 构造数据帧
        frame = b"\xeb\x90"  # 帧头
        frame += struct.pack("<H", length)  # 帧长度
        frame += struct.pack("<d", 0)  # 时间戳
        for value in params:
            frame += struct.pack("<f", value)  # 参数
        frame += struct.pack("<B", msg_type)  # 消息类型
        frame += struct.pack("<B", status)  # 状态
        frame += struct.pack("<B", loop_count)  # 循环计数
        frame += struct.pack("<B", sum & 0xFF)  # 校验和

        ser.write(frame)
        time.sleep(0.01)
