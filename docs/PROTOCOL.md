# Protocol and hardware notes

## HAF 700 EVO 2025 LCD

Observed under Windows:

    USB VID: 2516
    USB PID: 0228
    Bus description: HAF700 V2

The device exposes two USB/HID interfaces:

    MI_00
    MI_01

A vendor-defined HID interface is exposed on MI_00.

## ARGB controller

A separate controller is present:

    USB VID: 2516
    USB PID: 01C9
    Bus description: ARGB GEN-2

This device appears to be independent from the LCD.

## Windows software

Cooler Master MasterPlus 1.9.6:

- Detects the ARGB GEN-2 controller.
- Does not expose the HAF 700 EVO 2025 LCD.

Cooler Master MasterCTRL 1.5.2.243:

- Detects the HAF 700 EVO 2025.
- Controls the LCD successfully.
- Displays live GPU telemetry.

## Linux investigation plan

Initial discovery:

    lsusb -nn | grep -i 2516
    sudo lsusb -v -d 2516:0228
    ls -l /dev/hidraw*
    adb devices
    nvidia-smi

Next steps:

1. Enumerate USB interfaces under Linux.
2. Inspect HID report descriptors.
3. Determine whether ADB is exposed.
4. Inspect MasterCTRL communication.
5. Capture USB traffic under Windows if necessary.
6. Reproduce the LCD protocol under Linux.
7. Feed NVIDIA telemetry using NVML.
