#!/usr/bin/env python3

import glob
import os
import select
import sys

VID = "2516"
PID = "0228"

REPORT_COMMAND = 0x1E
REPORT_RESPONSE = 0x20
MAGIC = 0x5A
REPORT_SIZE = 1024


def find_haf_interface0():
    for path in sorted(glob.glob("/sys/class/hidraw/hidraw*")):
        dev_path = os.path.realpath(os.path.join(path, "device"))
        uevent = os.path.join(path, "device", "uevent")

        try:
            with open(uevent, "r", encoding="utf-8") as f:
                text = f.read().upper()
        except OSError:
            continue

        if f"HID_ID=0003:0000{VID}:0000{PID}" not in text:
            continue

        if ":1.0/" not in dev_path:
            continue

        return "/dev/" + os.path.basename(path)

    raise RuntimeError("No encontré HAF700 V2 interface 0")


def build_command(text):
    body = text.encode("ascii")

    packet = bytearray(REPORT_SIZE)
    packet[0] = REPORT_COMMAND
    packet[1] = MAGIC

    length = 4 + len(body) + 1
    packet[2:4] = length.to_bytes(2, "big")
    packet[4:4 + len(body)] = body

    checksum_pos = length - 1
    packet[checksum_pos] = sum(packet[2:checksum_pos]) & 0xFF
    packet[length] = MAGIC

    return packet


def decode_response(data):
    if len(data) != REPORT_SIZE:
        raise RuntimeError(
            f"Respuesta de {len(data)} bytes; esperaba {REPORT_SIZE}"
        )

    if data[0] != REPORT_RESPONSE:
        raise RuntimeError(
            f"Report ID inesperado: 0x{data[0]:02x}"
        )

    if data[1] != MAGIC:
        raise RuntimeError(
            f"Magic inesperado: 0x{data[1]:02x}"
        )

    length = int.from_bytes(data[2:4], "big")

    if length >= len(data):
        raise RuntimeError(f"Longitud inválida: {length}")

    if data[length] != MAGIC:
        raise RuntimeError("Terminador 0x5A no encontrado")

    return data[4:length - 1].decode(
        "ascii",
        errors="replace"
    )


def transact(command):
    dev = find_haf_interface0()
    packet = build_command(command)

    print(f"Device: {dev}")
    print(f"TX: {command.rstrip()}")

    fd = os.open(
        dev,
        os.O_RDWR | os.O_NONBLOCK
    )

    try:
        written = os.write(fd, packet)

        if written != REPORT_SIZE:
            raise RuntimeError(
                f"write() escribió {written} bytes"
            )

        ready, _, _ = select.select(
            [fd], [], [], 3
        )

        if not ready:
            raise TimeoutError(
                "Timeout esperando respuesta"
            )

        data = os.read(fd, REPORT_SIZE)

    finally:
        os.close(fd)

    return decode_response(data)


def main():
    command = "POST getSKUColor 1\r\n"

    try:
        response = transact(command)
    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr
        )
        return 1

    print()
    print("RX:")
    print(response)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
