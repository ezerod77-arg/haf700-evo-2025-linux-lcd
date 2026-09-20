# HAF 700 EVO 2025 Linux

Experimental Linux support for the LCD display included with the
Cooler Master HAF 700 EVO 2025.

## Known hardware

### LCD

- USB VID: `2516`
- USB PID: `0228`
- Windows description: `HAF700 V2`

### ARGB controller

- USB VID: `2516`
- USB PID: `01C9`
- Windows description: `ARGB GEN-2`

## Goal

Display NVIDIA GPU telemetry on the HAF 700 EVO 2025 front LCD under Linux.

Initial targets:

- GPU utilization
- GPU temperature
- GPU power
- VRAM usage

## Current status

Early reverse-engineering stage.

Cooler Master MasterCTRL 1.5.2.243 successfully detects and controls the
HAF 700 EVO 2025 LCD under Windows.

The older MasterPlus software detects the ARGB controller but does not expose
the HAF 700 EVO 2025 LCD.

Linux support for USB device `2516:0228` is under investigation.

## Development hardware

Current development system:

- Cooler Master HAF 700 EVO 2025
- NVIDIA GeForce RTX 5090
- AMD Ryzen 9 9950X

## Disclaimer

This project is not affiliated with or endorsed by Cooler Master.

No Cooler Master firmware, binaries, or proprietary assets are distributed
with this project.

## License

MIT
