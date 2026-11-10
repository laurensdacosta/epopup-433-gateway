# Recovery and hardware reference

## Proven working hardware

- ESP32-D0WD-V3, 4 MB flash; CC1101 at 433.96 MHz
- CS = GPIO 5
- GDO0 = GPIO 4 = RF transmitter
- GDO2 = GPIO 27 = RF receiver
- Original MQTT root = `home/OMG_rtl_433_ESP`
- Example lamp ON RF value = `12924884`, protocol 1, 24 bits, delay 409, repeat 5

> **Do not include passwords or full flash backups in the Git repository.**

## Recovery image: on the Mac only

The verified working **full-flash** backup was stored here:

`~/Documents/HomeAssistant/ESP32/epopup-full-backup.bin`

Its expected size is 4,194,304 bytes. Preserve an additional encrypted/offline copy.

When recovery is needed, confirm the correct USB serial port and the exact chip first.
Then, and **only for the full 4 MB backup**, you can restore it with:

```bash
~/.platformio/penv/bin/python -m esptool \
  --chip esp32 --port /dev/cu.usbserial-5AE10385061 \
  --baud 115200 \
  write_flash 0x0 \
  ~/Documents/HomeAssistant/ESP32/epopup-full-backup.bin
```

**Do not run this just to test**: it overwrites the device. Do not write an ordinary `firmware.bin` to address `0x0`; the latter is only for a known complete flash image.

## Verify an installed custom build

Send this via Home Assistant **Developer tools > Actions**:

```yaml
action: mqtt.publish
data:
  topic: home/OMG_rtl_433_ESP/commands/MQTTto433
  payload: '{"value":"12924884","protocol":1,"length":24,"delay":409,"repeat":5}'
```

Inspect the OpenMQTTGateway serial log and verify:

```text
C1101 spi Connection OK
RF_EMITTER_GPIO: 4
RF_RECEIVER_GPIO: 27
```

`MQTTtoRF OK` means the transmit routine ran; it does not on its own prove the lamp received RF.

After any test update, cut power and restart to confirm the GPIO values persist.
