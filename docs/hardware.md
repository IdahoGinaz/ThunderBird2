# Hardware
RaspBerry pi 4
RS485 CAN HAT
Octocoupler (8 Channel)
Sabrent 10 port USB HUb. Model HB-BU10
Android Head Unit.   Android 13 "B200 - Core 8 - Rom 64GB - LPDDR4 - Ram 4GB - 1280X720 - ID7"
2007 Nissan Atlas (Truck)
Sensors/radios: <!-- e.g. BME280 on I2C 0x76, SX1262 LoRa 915 MHz -->
Bluetooth Mini Keyboard and Dongle,
2 * USB Cameras (Arducam 1080P Low Light USB camera - "ID 0c45:0261 Microdia Arducam 1080P Low Light").  Keep in mind these may change.
1 * Logitech 720p USB camera.
1 Bluetooth OBDII engine code reader.


## Parts
| Part | Qty | Voltage / logic | Interface | Address / notes |
|------|-----|-----------------|-----------|-----------------|
| Raspberry Pi 4 | 1 | 3.3V logic | GPIO, I2C, SPI, UART | - |
| RS485 CAN HAT | 1 | 5V CAN signaling | I2C/SPI overlay | Nissan Atlas integration (TBD) |
| Octocoupler (8 Channel) | 1 | 5V inputs, 3.3V outputs | GPIO | GPIO pins TBD; not yet wired |
| Sabrent USB Hub (10-port) | 1 | 5V | USB 3.0 | Mounted in tray above head unit |
| Arducam 1080P USB camera | 2 | 5V | USB 3.0 | Vendor ID 0c45:0261 |
| Logitech 720p USB camera | 1 | 5V | USB 3.0 | Vendor ID TBD |
| Android Head Unit | 1 | 12V car power | USB + RCA video input | Android 13, 1280x720, 4GB RAM |
| Bluetooth Mini Keyboard | 1 | Battery (AA) | Bluetooth 5.0 | Wireless control |
| Bluetooth OBDII Reader | 1 | Car 12V (OBD-II port) | Bluetooth 4.0 | Optional future use |

## Pinout
| Device pin | Board pin (physical / GPIO) | Function | Notes |
|------------|-----------------------------|----------|-------|
| Octocoupler CH1-8 | TBD | Turn signals / truck lights | Not yet wired; plan redundancy with CAN |
| RS485 CAN HAT | TBD | CAN bus communication | For Nissan Atlas integration |
| Pi USB ports | A/B/C | USB hub + cameras | 4x type-A ports on Pi 4 |

## Power
- **Supply**: Official Raspberry Pi Power Supply (USB-C, model P0221)
- **Pi current**: ~3A typical (1.2A base + USB devices)
- **USB Hub**: Sabrent HB-BU10 (self-powered via barrel jack, not drawing from Pi)
- **Cameras**: Powered via USB hub (5V, ~500mA each estimated)
- **Total from Pi supply**: ~3.5A (safe with 5A supply)
- **Future**: Car 12V integration via DC-DC converter for automotive-grade resilience (TODO)

## Pins to avoid
- Pi: GPIO2/3 if I2C is used by something else; check enabled overlays
- Octocoupler wiring: Confirm all 8 channels before writing GPIO code

## Network / radio
- WiFi SSID (Home Network):  PoodleAttackArmy2 
- WiFi SSID (Fallback):  TB2
- CAN bus: Nissan Atlas (2007) — frequency/protocol TBD; check RS485 HAT documentation

## Devices on the network
| Name | Host/IP | Role | Login method |
|------|---------|------|--------------|
| Raspberry Pi | 192.168.178.103 | Main controller | SSH key (wolfpack user) |
| Android Head Unit | DHCP / static TBD | Video display | Physical buttons + BT keyboard |
| Dev PC (Windows) | DHCP | Development + deployment | SSH to Pi |
