---
name: rgb
description: View or change this PC's RGB lighting (RAM, motherboard, AMD Wraith Prism cooler, NZXT case lighting, G502 mouse) through OpenRGB. Use when the user runs /rgb or asks to change LED colours, lighting modes, brightness or effects. Fans and cooling belong to /cc.
argument-hint: "[lighting change, e.g. 'make the cooler ring red' or 'all LEDs #00FFAA']"
---

# RGB lighting (`/rgb`)

Request: $ARGUMENTS (if empty, run `rgbctl.py show` and summarise the current colours per device).

Companion to `/cc`, which handles fans and cooling. **OpenRGB owns all lighting.** Never set lighting through the CoolerControl API: the two would overwrite each other, and CoolerControl's lighting settings were cleared on purpose (the Gigabyte RGB controller is disabled in CoolerControl).

## How it's set up
- **Desired state:** `~/.config/OpenRGB/lighting.json` is the source of truth. It has one entry per OpenRGB device name: `mode`, `color` (hex, or comma-separated for multi-colour modes), optional `brightness` (0–100) and optional `zones: {"<zone name>": {"color": "..."}}`.
- **Helper:** `~/.claude/skills/rgb/rgbctl.py` edits that file, then re-applies **every** device in one `openrgb` call and saves the profile `~/.config/OpenRGB/lighting.orp`. Re-applying everything matters: a profile saved after setting only some devices would lose the others.
- **At login:** the systemd user service `openrgb-lighting.service` waits 10s, then runs `openrgb --noautoconnect --profile lighting`. The Wraith Prism (Direct mode), the RAM and the NZXT don't keep their colours through a power-off without it.

## Helper
```
rgbctl.py list                       # live devices, indices, modes, zones (~10–20s: OpenRGB scans)
rgbctl.py show                       # desired state
rgbctl.py set <device|all> [--mode M] [--color HEX[,HEX]] [--brightness N] [--zone Z]
rgbctl.py unset-zone <device> <zone> # remove a zone override (zone goes back to the device colour)
rgbctl.py apply [--dry-run]          # re-apply the file (e.g. after editing it by hand)
```
- `<device>` is a case-insensitive substring of the device name. Aliases: `ram`, `cooler`, `mobo`/`motherboard`, `case`, `mouse`. `all` means every device.
- `set` with `--color` and no `--zone` sets the whole device and removes its zone overrides.
- Zone overrides are sent as one `-c` list with a colour per LED (LEDs are mapped to zones by name prefix from `openrgb -l`). Don't use per-zone `-z`/`-c` pairs: the OpenRGB CLI applies only one `-z` per device, and in Direct mode any LED a command leaves out goes dark (found 2026-11-14 when the Wraith fan, then the ring, went off).
- `--mode static` on a device without Static (the RAM, the Wraith Prism) falls back to Direct automatically. Unsupported modes and bad hex values are rejected before anything changes.
- Device indices shift when devices appear or disappear (they did when the RAM was added). The helper resolves them on every run, so never hard-code `-d <idx>`.
- Both RAM sticks have the same name, so they're always set together. Setting them separately would need index-based handling added to the helper.

## Devices (as of 2026-11-14; confirm with `list`)
| Device (OpenRGB name) | Bus | Modes | Zones |
|---|---|---|---|
| Corsair Dominator Platinum ×2 (actually Vengeance RGB Pro `CMH32GX4M2E3200C16`) | SMBus `i2c-7` 0x5A/0x5B | Direct only | Corsair RAM Zone |
| X570 AORUS PRO WIFI | USB HID (IT8297) | Direct, Static, Breathing, Flashing, Color Cycle, Double Flash, Wave, Random, Wave 1–4 | 12V RGB Strips, D_LED1 Bottom, D_LED2 Top, Motherboard |
| AMD Wraith Prism | USB HID `2516:0051` | Direct, Breathing, Spectrum Cycle, Rainbow Wave, Bounce, Chase, Swirl | Logo, Fan, Ring |
| NZXT Smart Device V2 | USB HID | Direct, Static, Fading, Spectrum Cycle, Marquee, Cover Marquee, Alternating, Pulsing, Breathing, Candle, Starry Night, Super Rainbow, Rainbow Pulse, Rainbow Flow | Hue 2 Channel 1, Hue 2 Channel 2 |
| G502 HERO Gaming Mouse | USB receiver | Off, Direct, Static, Breathing, Spectrum Cycle | Primary Zone, Logo Zone |

Not controllable:
- **GPU logo** (Gigabyte RTX 2070 Super Windforce OC 3X, `1458:400d`): OpenRGB doesn't support this card. The user filed an upstream New Device issue on 2026-11-14. If maintainers ask for an I2C dump, only read: never write to the GPU's I2C buses (`i2c-0`…`6`) on a guess.
- **RAM access depends on** the kernel option `acpi_enforce_resources=lax` (added 2026-11-14 with `~/enable-ram-rgb.sh`; backup at `/etc/default/grub.bak`). If the RAM disappears from `list`, check `/proc/cmdline` first.

## Procedure
1. `rgbctl.py show` to see the current state, and `rgbctl.py list` if you need modes or zone names.
2. Make the change with `set` (or edit the JSON and run `apply`). Check that the command finishes with `applied; profile saved`.
3. You can't see the PC: ask the user to confirm it looks right. OpenRGB's listed "current" mode is a default, not read back from the hardware, so it proves nothing.
4. To make a change temporary (not kept at login), say so and avoid saving it: run `openrgb --noautoconnect -d <idx> ...` directly without `--save-profile`, and tell the user it will revert at the next login.
5. If you add or remove devices, or something changes about the setup, update the Devices table above.

Troubleshooting:
- **A device is missing from `list`:** another program may be holding it (e.g. an OpenRGB GUI or server). Check with `pgrep -a openrgb`.
- **The colours revert after reboot:** check `systemctl --user status openrgb-lighting.service`. If coolercontrold re-initialised the NZXT after the service ran, increase the `sleep`.
