#!/usr/bin/env python3
import glob
import io
import os
import random
import select
import subprocess
import time
from PIL import Image, ImageDraw, ImageFont

VID = "2516"
PID = "0228"
REPORT_SIZE = 1024
REPORT_COMMAND = 0x1E
REPORT_DATA = 0x1F
REPORT_RESPONSE = 0x20
MAGIC = 0x5A
DATA_MARKER = 0x5C
DATA_CHUNK = 1000
DATA_OFFSET = 24
JPEG_KIND = 1
REFRESH_SECONDS = 2.0

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def find_device():
    for path in sorted(glob.glob('/sys/class/hidraw/hidraw*')):
        try:
            text = open(os.path.join(path, 'device', 'uevent'), encoding='utf-8').read().upper()
        except OSError:
            continue
        dev_path = os.path.realpath(os.path.join(path, 'device'))
        if f'HID_ID=0003:0000{VID}:0000{PID}' in text and ':1.0/' in dev_path:
            return '/dev/' + os.path.basename(path)
    raise FileNotFoundError('HAF 700 EVO LCD HID interface not found')


def build_command(text):
    body = text.encode('ascii')
    packet = bytearray(REPORT_SIZE)
    packet[0] = REPORT_COMMAND
    packet[1] = MAGIC
    length = 4 + len(body) + 1
    packet[2:4] = length.to_bytes(2, 'big')
    packet[4:4+len(body)] = body
    checksum_pos = length - 1
    packet[checksum_pos] = sum(packet[2:checksum_pos]) & 0xFF
    packet[length] = MAGIC
    return packet


def set_realtime(fd):
    body = '{"enable":true}'
    cmd = (
        'POST realtimeDisplay 1\r\n'
        'SeqNumber=43\r\n'
        f'Date={int(time.time())}\r\n'
        'ContentType=json\r\n'
        f'ContentLength={len(body)}\r\n\r\n{body}'
    )
    os.write(fd, build_command(cmd))
    ready, _, _ = select.select([fd], [], [], 1.5)
    if ready:
        try:
            os.read(fd, REPORT_SIZE)
        except BlockingIOError:
            pass


def gpu_values():
    out = subprocess.check_output([
        'nvidia-smi',
        '--query-gpu=temperature.gpu,utilization.gpu,fan.speed',
        '--format=csv,noheader,nounits'
    ], text=True, timeout=3).splitlines()[0]
    temp, util, fan = [int(x.strip()) for x in out.split(',')[:3]]
    return temp, util, fan


def centered(draw, text, y, font, fill='white'):
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    draw.text(((480-width)//2, y), text, font=font, fill=fill)


def level_color(value, low, mid, high):
    # Continuous blue -> yellow -> red gradient.
    v = max(low, min(high, value))
    if v <= mid:
        t = (v - low) / max(1, mid - low)
        start = (0, 110, 255)
        end = (255, 220, 0)
    else:
        t = (v - mid) / max(1, high - mid)
        start = (255, 220, 0)
        end = (255, 35, 0)
    return tuple(round(a + (b-a)*t) for a, b in zip(start, end))


def render(temp, util, fan):
    img = Image.new('RGB', (480, 480), 'black')
    draw = ImageDraw.Draw(img)
    # Keep everything well inside the physically visible circular area.
    draw.ellipse((28, 28, 452, 452), outline=(90, 90, 90), width=3)
    centered(draw, 'GPU', 52, ImageFont.truetype(FONT_BOLD, 64))
    temp_color = level_color(temp, 30, 60, 85)
    util_color = level_color(util, 0, 50, 100)
    fan_color = level_color(fan, 0, 50, 100)
    centered(draw, f'{temp}°C', 122, ImageFont.truetype(FONT_BOLD, 108), fill=temp_color)

    # Bottom half: USO on the left, FAN on the right.
    label_font = ImageFont.truetype(FONT_BOLD, 42)
    value_font = ImageFont.truetype(FONT_BOLD, 58)
    def centered_in_half(text, y, font, x0, x1, fill):
        box = draw.textbbox((0, 0), text, font=font)
        width = box[2] - box[0]
        x = x0 + ((x1 - x0) - width) // 2
        draw.text((x, y), text, font=font, fill=fill)

    centered_in_half('USE', 266, label_font, 45, 240, 'white')
    centered_in_half(f'{util}%', 316, value_font, 45, 240, util_color)
    centered_in_half('FAN', 266, label_font, 240, 435, 'white')
    centered_in_half(f'{fan}%', 316, value_font, 240, 435, fan_color)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=92, optimize=True)
    return buf.getvalue()


def build_reports(data):
    transfer_id = random.randint(0, 59)
    total = (len(data) + DATA_CHUNK - 1) // DATA_CHUNK
    reports = []
    for index, offset in enumerate(range(0, len(data), DATA_CHUNK)):
        chunk = data[offset:offset+DATA_CHUNK]
        report = bytearray(REPORT_SIZE)
        report[0] = REPORT_DATA
        report[1] = DATA_MARKER
        report[2:4] = (len(chunk) + 20).to_bytes(2, 'big')
        report[4] = transfer_id
        report[5:7] = total.to_bytes(2, 'big')
        report[7:9] = index.to_bytes(2, 'big')
        report[9] = JPEG_KIND
        report[DATA_OFFSET:DATA_OFFSET+len(chunk)] = chunk
        reports.append(report)
    return reports


def drain(fd):
    while True:
        ready, _, _ = select.select([fd], [], [], 0)
        if not ready:
            break
        try:
            os.read(fd, REPORT_SIZE)
        except BlockingIOError:
            break


def run():
    last = None
    while True:
        fd = None
        try:
            dev = find_device()
            fd = os.open(dev, os.O_RDWR | os.O_NONBLOCK)
            set_realtime(fd)
            while True:
                temp, util, fan = gpu_values()
                current = (temp, util, fan)
                # Always resend: the HAF realtime watchdog returns to offline media
                # after roughly five seconds even if the image has not changed.
                jpeg = render(*current)
                for report in build_reports(jpeg):
                    os.write(fd, report)
                last = current
                time.sleep(0.06)
                drain(fd)
                time.sleep(REFRESH_SECONDS)
        except Exception as exc:
            print(f'haf_gpu_display: {exc}', flush=True)
            time.sleep(3)
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass


if __name__ == '__main__':
    run()
