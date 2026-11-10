#!/usr/bin/env python3
"""Reject risky changes to the Epopup hardware/OTA profile before building."""
import argparse
import configparser
import pathlib
import re

EXPECTED = {
    "ZgatewayRF": '"RF"',
    "ZgatewayRF2": '"RF2"',
    "ZgatewayRTL_433": '"RTL_433"',
    "ZradioCC1101": '"CC1101"',
    "Gateway_Name": '"OMG_multi_receiver"',
    "valueAsATopic": "true",
    "RF_CC1101": '"CC1101"',
    "RF_MODULE_CS": "5",
    "RF_MODULE_GDO0": "4",
    "RF_MODULE_GDO2": "27",
    "RF_EMITTER_GPIO": "4",
    "RF_RECEIVER_GPIO": "27",
}


def check_profile(profile: pathlib.Path) -> None:
    contents = profile.read_text(encoding="utf-8")
    parser = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=(";",))
    parser.optionxform = str
    parser.read_string(contents)
    assert "env:epopup-433" in parser, "Missing custom PlatformIO environment"
    section = parser["env:epopup-433"]
    assert section.get("extends", "").strip() == "env:esp32dev-multi_receiver", "Unexpected base profile"
    flags = section["build_flags"].splitlines()
    assert any("${com-esp32.build_flags}" in line for line in flags), "Missing upstream ESP32 common flags"
    macros = {}
    undefines = set()
    for line in flags:
        line = line.strip()
        if not line or line.startswith(";") or line.startswith("#") or line.startswith("${"):
            continue
        # PlatformIO allows quoted -D/-U args, but never allow duplicate macros.
        clean = line.strip("'")
        if clean.startswith("-D"):
            key, sep, value = clean[2:].partition("=")
            assert sep, f"Invalid define: {line}"
            assert key not in macros, f"Duplicate define: {key}"
            macros[key] = value
        elif clean.startswith("-U"):
            undefines.add(clean[2:])
        else:
            raise AssertionError(f"Unexpected flag (review required): {line}")
    assert macros == EXPECTED, f"Unexpected build flags: expected {EXPECTED}, got {macros}"
    assert undefines == {"MQTT_HTTPS_FW_UPDATE"}, f"OTA guard missing or modified: {undefines}"
    assert not re.search(r"(?im)^\s*['\"]?-D(?:wifi_password|MQTT_PASS|OTA_PASSWORD)", contents), "Don't put secrets in repository"
    print("PASS: CC1101 CS=5, TX/GDO0=4, RX/GDO2=27; generic MQTT OTA disabled")


def check_upstream(root: pathlib.Path) -> None:
    pio = root / "platformio.ini"
    envs = root / "environments.ini"
    assert pio.exists() and envs.exists(), "Upstream checkout is not a PlatformIO OpenMQTTGateway project"
    pio_txt = pio.read_text(encoding="utf-8")
    assert "*_env.ini" in pio_txt, "Upstream no longer imports custom *_env.ini files"
    upstream = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=(";",))
    upstream.optionxform = str
    upstream.read(envs, encoding="utf-8")
    assert "env:esp32dev-multi_receiver" in upstream, "Upstream removed the multi-receiver target"
    base = upstream["env:esp32dev-multi_receiver"]
    assert base.get("board", "").strip() == "esp32dev", "Unexpected board"
    deps = base.get("lib_deps", "")
    for fragment in ("libraries.rc-switch", "libraries.smartrc-cc1101-driver-lib", "libraries.rtl_433_ESP", "libraries.newremoteswitch"):
        assert fragment in deps, f"Missing upstream dependency: {fragment}"
    print("PASS: upstream PlatformIO project supports expected board, modules and custom overlay")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="firmware/epopup_env.ini", type=pathlib.Path)
    ap.add_argument("--upstream", type=pathlib.Path)
    args = ap.parse_args()
    check_profile(args.profile)
    if args.upstream:
        check_upstream(args.upstream)
