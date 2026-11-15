#!/usr/bin/env python3
"""Manage this PC's RGB lighting through the OpenRGB CLI.

The desired state lives in ~/.config/OpenRGB/lighting.json (source of truth).
Every `apply` re-applies ALL devices from that file and saves the OpenRGB
profile that the login service (openrgb-lighting.service) loads.

  rgbctl.py list                         devices, indices, modes, zones (live)
  rgbctl.py show                         current desired state (JSON)
  rgbctl.py set <device|all> [--mode M] [--color HEX[,HEX...]] [--brightness N]
                [--zone ZONE]            update desired state, then apply
  rgbctl.py unset-zone <device> <zone>   drop a per-zone override, then apply
  rgbctl.py apply [--dry-run]            apply desired state + save profile

<device> is a case-insensitive substring of the OpenRGB device name ("ram" is
an alias for the Corsair modules). Devices with the same name (RAM sticks) are
all set together.
"""
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

CONFIG = Path.home() / ".config/OpenRGB/lighting.json"
PROFILE = "lighting"
OPENRGB = ["openrgb", "--noautoconnect"]
ALIASES = {"ram": "corsair", "cooler": "wraith", "mobo": "aorus",
           "motherboard": "aorus", "case": "nzxt", "mouse": "g502"}
HEX = re.compile(r"^#?[0-9A-Fa-f]{6}$")


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def run(args, timeout=120):
    r = subprocess.run(OPENRGB + args, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def detect():
    """Return list of {idx, name, modes, current_mode, zones} from --list-devices."""
    rc, out = run(["--list-devices"])
    devs, cur = [], None
    for line in out.splitlines():
        m = re.match(r"^(\d+): (.+)$", line)
        if m:
            cur = {"idx": int(m.group(1)), "name": m.group(2).strip(),
                   "modes": [], "current_mode": None, "zones": [], "leds": []}
            devs.append(cur)
            continue
        if cur is None:
            continue
        s = line.strip()
        if s.startswith("Modes:"):
            for tok in shlex.split(s[len("Modes:"):]):
                if tok.startswith("[") and tok.endswith("]"):
                    tok = tok[1:-1]
                    cur["current_mode"] = tok
                cur["modes"].append(tok)
        elif s.startswith("Zones:"):
            cur["zones"] = shlex.split(s[len("Zones:"):])
        elif s.startswith("LEDs:"):
            cur["leds"] = shlex.split(s[len("LEDs:"):])
    if not devs:
        die(f"OpenRGB found no devices (exit {rc}). Output:\n{out[-2000:]}")
    return devs


def load():
    if not CONFIG.exists():
        die(f"{CONFIG} missing")
    return json.loads(CONFIG.read_text())


def save(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2) + "\n")


def norm_color(c):
    parts = [p.strip() for p in c.split(",")]
    for p in parts:
        if not HEX.match(p):
            die(f"bad colour {p!r}: use 6-digit hex like 7F00FF")
    return ",".join(p.lstrip("#").upper() for p in parts)


def match_names(cfg, query, devs):
    names = sorted({d["name"] for d in devs} | set(cfg["devices"]))
    if query.lower() == "all":
        return names
    q = ALIASES.get(query.lower(), query).lower()
    hits = [n for n in names if q in n.lower()]
    if not hits:
        die(f"no device matches {query!r}. Known: {', '.join(names)}")
    return hits


def resolve_mode(dev, mode):
    lower = {m.lower(): m for m in dev["modes"]}
    if mode.lower() in lower:
        return lower[mode.lower()]
    if mode.lower() == "static" and "direct" in lower:
        return lower["direct"]  # e.g. Wraith Prism / RAM have no Static
    die(f"{dev['name']} has no mode {mode!r}. Modes: {', '.join(dev['modes'])}")


def build(cfg, devs):
    args, notes = [], []
    for d in devs:
        want = cfg["devices"].get(d["name"])
        if want is None:
            notes.append(f"skip #{d['idx']} {d['name']}: not in {CONFIG.name}")
            continue
        mode = resolve_mode(d, want.get("mode", "static"))
        dargs = ["-d", str(d["idx"]), "-m", mode]
        if "brightness" in want:
            dargs += ["-b", str(want["brightness"])]
        zones = want.get("zones") or {}
        if zones:
            # One -c list with a colour per LED, in LED order. The OpenRGB CLI
            # applies only one -z per device, and in Direct mode any LED left
            # out of a command goes dark, so per-zone -z/-c pairs don't work.
            base = (want.get("color") or "000000").split(",")[0]
            per_led = []
            for led in d["leds"]:
                zname = next((z for z in sorted(d["zones"], key=len, reverse=True)
                              if led.lower().startswith(z.lower())), None)
                if zname is None:
                    die(f"{d['name']}: can't tell which zone LED {led!r} belongs to "
                        f"(zones {d['zones']}); zone overrides need LED names that start with the zone name")
                per_led.append(zones.get(zname, {}).get("color", base).split(",")[0])
            dargs += ["-c", ",".join(per_led)]
            unknown = set(zones) - set(d["zones"])
            if unknown:
                notes.append(f"{d['name']}: unknown zone(s) {sorted(unknown)}; zones are {d['zones']}")
        elif want.get("color"):
            dargs += ["-c", want["color"]]
        args += dargs
    for name in cfg["devices"]:
        if not any(d["name"] == name for d in devs):
            notes.append(f"configured but not detected: {name}")
    return args, notes


def cmd_apply(dry=False):
    cfg, devs = load(), detect()
    args, notes = build(cfg, devs)
    for n in notes:
        print("note:", n)
    full = args + ["--save-profile", PROFILE]
    print("openrgb --noautoconnect " + " ".join(shlex.quote(a) for a in full))
    if dry:
        return
    rc, out = run(full, timeout=180)
    out = "\n".join(l for l in out.splitlines() if l.strip())
    if out:
        print(out[-3000:])
    if rc != 0:
        die(f"openrgb exited {rc}")
    print(f"applied; profile saved to ~/.config/OpenRGB/{PROFILE}.orp")


def cmd_list():
    for d in detect():
        print(f"#{d['idx']} {d['name']}")
        # The bracketed "current" mode in OpenRGB's listing is its default, not read
        # back from hardware, so it isn't shown here.
        print(f"    modes: {', '.join(d['modes'])}")
        print(f"    zones: {', '.join(d['zones'])}")


def cmd_set(argv):
    if not argv:
        die("usage: set <device|all> [--mode M] [--color HEX] [--brightness N] [--zone Z]")
    query, opts, i = argv[0], {}, 1
    while i < len(argv):
        k = argv[i]
        if k not in ("--mode", "--color", "--brightness", "--zone") or i + 1 >= len(argv):
            die(f"bad option {k!r}")
        opts[k[2:]] = argv[i + 1]
        i += 2
    if not ({"mode", "color", "brightness"} & opts.keys()):
        die("nothing to set")
    cfg, devs = load(), detect()
    for name in match_names(cfg, query, devs):
        entry = cfg["devices"].setdefault(name, {"mode": "static"})
        live = [d for d in devs if d["name"] == name]
        if "mode" in opts and live:
            resolve_mode(live[0], opts["mode"])  # validate early
        if "zone" in opts:
            if live and opts["zone"] not in live[0]["zones"]:
                die(f"{name} has no zone {opts['zone']!r}. Zones: {live[0]['zones']}")
            if "color" in opts:
                entry.setdefault("zones", {}).setdefault(opts["zone"], {})["color"] = norm_color(opts["color"])
        elif "color" in opts:
            entry["color"] = norm_color(opts["color"])
            entry.pop("zones", None)  # a whole-device colour replaces zone overrides
        if "mode" in opts:
            entry["mode"] = opts["mode"].lower()
        if "brightness" in opts:
            b = int(opts["brightness"])
            if not 0 <= b <= 100:
                die("brightness must be 0-100")
            entry["brightness"] = b
        print(f"{name}: {json.dumps(entry)}")
    save(cfg)
    cmd_apply()


def cmd_unset_zone(argv):
    if len(argv) != 2:
        die("usage: unset-zone <device> <zone>")
    cfg, devs = load(), detect()
    for name in match_names(cfg, argv[0], devs):
        z = cfg["devices"].get(name, {}).get("zones", {})
        if z.pop(argv[1], None) is not None:
            print(f"{name}: removed zone override {argv[1]!r}")
        if not z:
            cfg["devices"].get(name, {}).pop("zones", None)
    save(cfg)
    cmd_apply()


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__)
    elif a[0] == "list":
        cmd_list()
    elif a[0] == "show":
        print(json.dumps(load(), indent=2))
    elif a[0] == "apply":
        cmd_apply(dry="--dry-run" in a)
    elif a[0] == "set":
        cmd_set(a[1:])
    elif a[0] == "unset-zone":
        cmd_unset_zone(a[1:])
    else:
        die(f"unknown command {a[0]!r}")


if __name__ == "__main__":
    main()
