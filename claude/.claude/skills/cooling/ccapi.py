#!/usr/bin/env python3
"""Minimal CoolerControl API helper.

Usage:
  ccapi.py status                 # temps, fan duty/RPM for every device
  ccapi.py get <path>             # GET  e.g. /profiles, /functions, /devices
  ccapi.py put <path> <json|@file>
  ccapi.py post <path> <json|@file>
  ccapi.py delete <path>
  ccapi.py backup                 # save /profiles + /functions to ~/.config/coolercontrol-api/backups/

The token is read from ~/.config/coolercontrol-api/token and never printed.
"""
import json, os, ssl, sys, time, urllib.request, urllib.error

BASE = "https://127.0.0.1:11987"
TOKEN_FILE = os.path.expanduser("~/.config/coolercontrol-api/token")
BACKUP_DIR = os.path.expanduser("~/.config/coolercontrol-api/backups")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE  # daemon uses a self-signed cert on localhost


def call(method, path, body=None):
    with open(TOKEN_FILE) as f:
        token = f.read().strip()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=10) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def load_body(arg):
    if arg.startswith("@"):
        with open(arg[1:]) as f:
            return json.load(f)
    return json.loads(arg)


def status():
    code, devs = call("GET", "/devices")
    names = {d["uid"]: d["name"] for d in devs["devices"]}
    labels = {d["uid"]: {k: v.get("label", k) for k, v in (d["info"].get("temps") or {}).items()}
              for d in devs["devices"]}
    code, st = call("POST", "/status", {})
    for d in st["devices"]:
        s = d["status_history"][-1]
        temps = [f"{labels[d['uid']].get(t['name'], t['name'])}={t['temp']:.0f}C" for t in s.get("temps", [])]
        fans = [f"{c['name']}={c['duty']:.0f}%/{c['rpm']}rpm" for c in s.get("channels", [])
                if c.get("rpm") is not None]
        if temps or fans:
            print(f"{names[d['uid']]} [{d['uid'][:8]}]: " + "  ".join(temps + fans))


def backup():
    os.makedirs(BACKUP_DIR, mode=0o700, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for p in ("profiles", "functions"):
        code, data = call("GET", "/" + p)
        path = os.path.join(BACKUP_DIR, f"{stamp}-{p}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(path)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    cmd = a[0]
    if cmd == "status":
        status()
    elif cmd == "backup":
        backup()
    elif cmd in ("get", "delete"):
        code, data = call(cmd.upper(), a[1])
        print(json.dumps(data, indent=2) if not isinstance(data, str) else data)
        print(f"HTTP {code}", file=sys.stderr)
    elif cmd in ("put", "post"):
        code, data = call(cmd.upper(), a[1], load_body(a[2]))
        print(json.dumps(data, indent=2) if not isinstance(data, str) else data)
        print(f"HTTP {code}", file=sys.stderr)
    else:
        print(__doc__); sys.exit(1)


if __name__ == "__main__":
    main()
