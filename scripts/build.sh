#!/usr/bin/env bash
# Build a custom Epopup firmware from a selected official OpenMQTTGateway release.
# Does NOT upload to a device, modify MQTT, or publish releases.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_TAG="${1:-v1.8.1}"
if [[ ! "$UPSTREAM_TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "ERROR: specify an official stable release tag (e.g. v1.8.1)" >&2
  exit 1
fi

PIO_BIN="${PIO_BIN:-pio}"
"${PIO_BIN}" --version
python3 "$ROOT/scripts/validate.py" --profile "$ROOT/firmware/epopup_env.ini"

CHECKOUT_DIR="$ROOT/.build/OpenMQTTGateway"
if [[ -e "$CHECKOUT_DIR" ]]; then
  echo "Removing previous temporary upstream checkout"
  rm -rf "$CHECKOUT_DIR"
fi
mkdir -p "$ROOT/.build"
git clone --depth 1 --branch "$UPSTREAM_TAG" \
  https://github.com/1technophile/OpenMQTTGateway.git "$CHECKOUT_DIR"

python3 "$ROOT/scripts/validate.py" --profile "$ROOT/firmware/epopup_env.ini" --upstream "$CHECKOUT_DIR"
cp "$ROOT/firmware/epopup_env.ini" "$CHECKOUT_DIR/epopup_env.ini"

"${PIO_BIN}" run --project-dir "$CHECKOUT_DIR" -e epopup-433

OUT="$ROOT/dist/${UPSTREAM_TAG}"
mkdir -p "$OUT"
cp "$CHECKOUT_DIR/.pio/build/epopup-433/firmware.bin" "$OUT/epopup-433-firmware.bin"
for optional_file in bootloader.bin partitions.bin; do
  if [[ -f "$CHECKOUT_DIR/.pio/build/epopup-433/$optional_file" ]]; then
    cp "$CHECKOUT_DIR/.pio/build/epopup-433/$optional_file" "$OUT/$optional_file"
  fi
done
printf '%s\n' "$UPSTREAM_TAG" > "$OUT/upstream-tag.txt"
git -C "$CHECKOUT_DIR" rev-parse HEAD > "$OUT/upstream-commit.txt"
(
  cd "$OUT"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 *.bin > SHA256SUMS
  else
    sha256sum *.bin > SHA256SUMS
  fi
)

echo
printf 'Build complete: %s\n' "$OUT/epopup-433-firmware.bin"
echo 'Custom firmware is NOT installed on your ESP32.'
