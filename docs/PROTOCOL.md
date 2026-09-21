# Protocol and hardware notes

## HAF 700 EVO 2025 LCD

Confirmed device identity:

    USB VID: 2516
    USB PID: 0228
    Product: HAF700 V2

This is the HAF 700 EVO 2025 front LCD device.

It is different from earlier HAF 700 EVO implementations that use other
USB product IDs and different transports.

## USB interfaces

Confirmed under both Windows and Linux.

### Interface 0

Vendor-defined HID interface used for LCD communication.

    Interface: 0
    Class: HID

    Endpoint 0x81 IN
    Type: Interrupt
    Max packet size: 1024 bytes

    Endpoint 0x02 OUT
    Type: Interrupt
    Max packet size: 1024 bytes

Under Linux this interface appears as a hidraw device, for example:

    /dev/hidraw8

The exact hidraw number is dynamic and must not be hardcoded.

### Interface 1

Secondary HID interface.

    Interface: 1
    Class: HID

    Endpoint 0x83 IN
    Type: Interrupt
    Max packet size: 8 bytes

Windows exposes this interface as mouse-compatible HID.

## HID report descriptor

The Interface 0 HID report descriptor declares:

    Report ID 0x01
    FEATURE
    6 bytes payload

    Report ID 0x02
    OUTPUT
    1 byte payload

    Report ID 0x14
    FEATURE
    47 bytes payload

    Report ID 0x1E
    OUTPUT
    1023 bytes payload

    Report ID 0x1F
    OUTPUT
    1023 bytes payload

    Report ID 0x20
    INPUT
    1023 bytes payload

Including the Report ID byte, the large reports are therefore:

    1024 bytes total

Observed purpose:

    0x1E = command/control request
    0x1F = LCD image/frame transport
    0x20 = command/control response

## Control protocol

Control requests use HID Report ID 0x1E.

Observed layout:

    Byte 0      HID Report ID = 0x1E
    Byte 1      0x5A
    Byte 2-3    big-endian length
    Byte 4...   ASCII command / headers / optional JSON
    checksum    sum8
    terminator  0x5A
    remaining   zero padding to 1024 bytes

The checksum has been verified against captured MasterCTRL traffic.

Formula:

    checksum = sum(bytes from length field through end of body) & 0xff

Example request observed and successfully reproduced under Linux:

    POST getSKUColor 1\r\n

Linux-generated request:

    1e 5a 00 19
    50 4f 53 54 20 67 65 74 53 4b 55 43 6f 6c 6f 72 20 31 0d 0a
    19
    5a

The device replied successfully with HID Report ID 0x20:

    1 200
    AckNumber=1
    ContentType=json
    ContentLength=12

    {"color":""}

This proves direct communication from Linux to the HAF700 V2 without
MasterCTRL, Windows, or Wine.

## Response protocol

Responses use HID Report ID 0x20.

Observed layout:

    Byte 0      HID Report ID = 0x20
    Byte 1      0x5A
    Byte 2-3    big-endian length
    Byte 4...   ASCII response / headers / optional JSON
    trailer     0x00
    terminator  0x5A
    remaining   zero padding to 1024 bytes

Typical response:

    1 200
    AckNumber=<n>
    ContentType=json
    ContentLength=<n>

    {...}

## Image transport

LCD image data uses HID Report ID 0x1F.

Windows USB captures show JPEG data fragmented into 1024-byte HID reports.

A complete JPEG image was reconstructed successfully from captured HAF
traffic.

Confirmed image dimensions:

    480 x 480

This means the physical USB transport does not send the Windows shared-memory
framebuffer directly as raw RGBA pixels.

Observed architecture is approximately:

    MasterCTRL renderer
        |
        v
    Windows shared memory
        |
        v
    CMAgent
        |
        +--> encodes / prepares display image
        |
        v
    HID Report 0x1F
        |
        v
    HAF700 V2 LCD

Observed MasterCTRL streaming was approximately 12-13 frames per second.
This is an observation, not yet established as the device maximum.

## Windows shared memory

MasterCTRL references the named shared-memory buffer:

    Global\LCDHAF700V2MATRIXSSR480X480

Size:

    921600 bytes

Which equals:

    480 * 480 * 4

This strongly indicates a 480x480 4-byte-per-pixel renderer buffer.

Exact channel order is not yet confirmed.

## Brightness command

Captured MasterCTRL traffic contains commands of the form:

    POST brightness 1
    SeqNumber=<n>
    Date=<n>
    ContentType=json
    ContentLength=12

    {"value":80}

The corresponding device response is HTTP-like:

    1 200
    AckNumber=<n>
    ContentType=
    ContentLength=0

The exact behavior and sequence-number relationship still needs further
investigation before implementing brightness control in the Linux client.

## Realtime mode

Captured MasterCTRL traffic periodically sends commands including:

    STATE timestamp 1

and:

    POST realtimeDisplay 1

    {"enable":true}

These appear related to realtime display operation / keepalive behavior.

The exact requirements for maintaining realtime image mode are still under
investigation.

## Cooler Master Windows software

### MasterPlus 1.9.6

- Detects the ARGB GEN-2 controller.
- Does not expose the HAF 700 EVO 2025 LCD.

### MasterCTRL 1.5.2.243

- Detects the device as HAF 700 EVO 2025.
- Controls the LCD.
- Displays live telemetry.
- Uses CMAgent as the physical-device backend.

Relevant internal model/state identifiers observed:

    Model: HAF 700 EVO 2025
    Model ID: 0f74e733-aaa3-50c3-a421-b11e54b0881a

    Electron state ID: haf700-v2
    CMAgent data model key: haf700v2

The separate "core-lcd" model must not be confused with HAF700 V2.

## CMAgent observations

CMAgent contains a shared LCD implementation named:

    LCDATMOSV2SubDevice

Its FetchStates logic includes:

    atmos-v2
    haf700-v2
    ion360-v2

Relevant methods observed include:

    GetCapabilities
    GetDisplayMode
    SetDisplayMode
    GetBrightness
    SetBrightness
    GetRotation
    SetRotation
    SendKeepAlive
    SendSubCommand
    SSRCommandResponse
    SaveConfig
    Reset
    ResetConfig

CMAgent also contains the diagnostic string:

    Cannot open USB devices! But keeping shared memory work

This confirms that the USB device and shared-memory renderer are separate
layers in the implementation.

The binary also contains the symbol/string:

    sum8

Captured traffic confirms that an 8-bit additive checksum is used by
0x1E control requests.

## ARGB controller

A separate Cooler Master device is present:

    USB VID: 2516
    USB PID: 01C9
    Product: ARGB GEN-2

This controller is independent from the HAF700 V2 LCD device.

Under the tested system:

    HAF700 V2      = 2516:0228
    ARGB GEN-2     = 2516:01c9

## Linux support

Linux detects the LCD normally using the kernel HID stack.

Confirmed:

    lsusb:
    2516:0228 Cooler Master Co., Ltd. HAF700 V2

Direct userspace access works through:

    /dev/hidraw*

A udev rule is included in this repository:

    udev/99-haf700-v2.rules

The current Linux probe:

    tools/haf_probe.py

automatically locates Interface 0 and successfully performs a real
request/response transaction with the device.

Example:

    $ ./tools/haf_probe.py

    Device: /dev/hidraw8
    TX: POST getSKUColor 1

    RX:
    1 200
    AckNumber=1
    ContentType=json
    ContentLength=12

    {"color":""}

No custom kernel driver is currently required.

## Next protocol milestones

1. Decode additional read-only commands:
   - GetBrightness
   - GetCapabilities
   - GetDisplayMode
   - GetRotation

2. Implement structured request/response parsing.

3. Confirm sequence and acknowledgement behavior.

4. Reproduce a safe SetBrightness operation.

5. Implement Report 0x1F JPEG/frame transmission.

6. Display a Linux-generated 480x480 image.

7. Implement realtime CPU/GPU telemetry rendering.

8. Run the display controller as a systemd user service.

9. Avoid hardcoding hidraw device numbers.

## Publication notes

Do not commit proprietary Cooler Master binaries, extracted application
assets, or proprietary source material.

Only publish independently written code, protocol observations, identifiers,
and minimal behavioral information required for interoperability.
