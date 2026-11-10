# Epopup 433MHz gateway — custom OpenMQTTGateway firmware

Private configuration and build pipeline for an ESP32-D0WD-V3 (4 MB flash) with CC1101 controlling an Epopup pendant lamp at **433.96 MHz**.

**Why:** the upstream `esp32dev-multi_receiver` firmware defaults to GDO0 / RF TX on **GPIO 12**, but this gateway is wired to **GPIO 4**. Installing upstream's stock firmware from Home Assistant breaks RF transmission even though MQTT and the CC1101 still look healthy.

## Fixed configuration

| Function | GPIO |
|---|---:|
| CC1101 CS | 5 |
| CC1101 GDO0 / RF transmitter | **4** |
| CC1101 GDO2 / RF receiver | **27** |

Profile: [`firmware/epopup_env.ini`](firmware/epopup_env.ini). It starts from `esp32dev-multi_receiver`, **replaces** its build flags to avoid inheriting upstream's GPIO 12 definition, and disables generic `MQTT_HTTPS_FW_UPDATE` in the custom firmware. The normal MQTT control path and web UI remain enabled.

This project intentionally contains **no WiFi, MQTT or OTA passwords**, no full flash backup, and no scheduled firmware deployment.

## GitHub Actions

1. Create a **private** empty repository under your personal account (`laurensdacosta`, not an organization).
2. Push this project to its `main` branch (commands below).
3. Open **Actions > Build Epopup custom OpenMQTTGateway firmware > Run workflow**.
4. Start with `upstream_tag = v1.8.1` to match the known working major configuration. Newer release tags (e.g. `v1.9.1`) can be built **manually** later.
5. Download the `epopup-firmware-<tag>` run artifact; it contains the application `epopup-433-firmware.bin`, upstream commit, tag and SHA-256 checksums.
6. **Do not flash a new upstream release just because it compiled.** Save the current full-flash backup, compare configuration changes, flash when physically available to recover, test lamp ON/OFF, GPIO 4/27, and cold reboot.

The workflow never updates the ESP32 and does not create a public release. GitHub Actions artifacts expire after 90 days: download important successful builds to a private backup location.

### Push to your personal GitHub account

```bash
# After downloading and unzipping this project:
cd epopup-433-gateway
git init -b main
git add .
git commit -m 'Initial custom Epopup gateway build pipeline'
# Create a PRIVATE repo named epopup-433-gateway in GitHub first.
git remote add origin git@github.com:laurensdacosta/epopup-433-gateway.git
git push -u origin main
```

Nothing is written to GitHub until you push it yourself.

## Build locally on macOS

Needs Git, internet, Python 3 and PlatformIO CLI. If PlatformIO isn't in PATH, set `PIO_BIN="$HOME/.platformio/penv/bin/pio"`.

```bash
PIO_BIN="$HOME/.platformio/penv/bin/pio" bash scripts/build.sh v1.8.1
```

This clones the chosen upstream tag into `.build/OpenMQTTGateway`, copies our custom configuration to `epopup_env.ini` (supported by upstream `platformio.ini`), and compiles `-e epopup-433`.

Result: `dist/v1.8.1/epopup-433-firmware.bin`, plus checksum and upstream commit SHA.

### Flash locally using PlatformIO (deliberately manual)

After building, connect the ESP32 by USB, find its current port with `pio device list`, and upload the **same** custom environment:

```bash
"$HOME/.platformio/penv/bin/pio" run \
  --project-dir .build/OpenMQTTGateway \
  -e epopup-433 -t upload \
  --upload-port /dev/cu.usbserial-5AE10385061
```

The USB port is an example from the known device; verify it each time. Existing WiFi/MQTT settings are generally retained by app firmware updates but verify after flashing.

### Why no automatic OTA update from a private GitHub repository?

The stock Home Assistant `SYS: Firmware Update` feature installs upstream's **generic** binary and must remain disabled. Artifacts from a private repository are not anonymous firmware URLs that a bare ESP32 can download. This repository therefore **builds only**. Future controlled OTA can be added using a private, reachable firmware-serving endpoint and explicit authentication/TLS review; do not repurpose the stock update button.

The custom profile disables the generic MQTT HTTPS firmware update feature to avoid installing a stock binary accidentally. Consequently **that particular firmware-update API is not an OTA path** for the custom build. Keep USB access and the full-flash backup available.

## Safety checks

Before compiling, [`scripts/validate.py`](scripts/validate.py) verifies the exact GPIO, module defines and MQTT OTA disable flag, and checks that upstream still has the expected board and supporting dependencies. If upstream changes its environment layout, the build fails and requires manual review. The validation is a guard, not a hardware test.

## Documentation and recovery

- [Recovery steps, backup path and test MQTT payload](docs/RECOVERY.md)
- [Upstream custom PlatformIO environments](https://docs.openmqttgateway.com/upload/builds.html)
- [Upstream MQTT firmware update behavior](https://docs.openmqttgateway.com/use/gateway.html)
- [Upstream project](https://github.com/1technophile/OpenMQTTGateway)
