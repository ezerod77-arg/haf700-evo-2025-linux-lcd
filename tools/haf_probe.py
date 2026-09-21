#!/usr/bin/env python3

import argparse
import glob
import os
import select
import sys
import time

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


def set_brightness(value):
    if not 0 <= value <= 100:
        raise ValueError(
            "brightness debe estar entre 0 y 100"
        )

    body = f'{{"value":{value}}}'

    command = (
        "POST brightness 1\r\n"
        "SeqNumber=44\r\n"
        f"Date={int(time.time())}\r\n"
        "ContentType=json\r\n"
        f"ContentLength={len(body)}\r\n"
        "\r\n"
        f"{body}"
    )

    return transact(command)


def main():
    parser = argparse.ArgumentParser(
        description="HAF 700 EVO 2025 Linux HID client"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    subparsers.add_parser(
        "probe",
        help="Test communication with HAF700 V2"
    )

    brightness_parser = subparsers.add_parser(
        "brightness",
        help="Set LCD brightness"
    )

    brightness_parser.add_argument(
        "value",
        type=int,
        metavar="0-100",
        help="Brightness percentage"
    )

    args = parser.parse_args()

    try:
        if args.command == "probe":
            response = transact(
                "POST getSKUColor 1\r\n"
            )

        elif args.command == "brightness":
            response = set_brightness(
                args.value
            )

        else:
            parser.error(
                "comando desconocido"
            )

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
