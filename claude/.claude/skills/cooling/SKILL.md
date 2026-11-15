---
name: cooling
description: View or change this PC's fan curves, fan profiles and cooling settings through the CoolerControl daemon API (GPU fan, NZXT case fans). Use when the user runs /cooling or asks to check temperatures/fan speeds or tweak fan curves, profiles or CoolerControl settings.
argument-hint: "[what to check or change, e.g. 'make the case fans quieter']"
---

# Cooling (`/cooling`)

The user prefers fan changes made through the API instead of the CoolerControl UI.
Request: $ARGUMENTS (if empty, run `status` and summarise temps and fan speeds).

## Access
- Daemon: `coolercontrold` (4.3.1 when this was written) at `https://127.0.0.1:11987`, self-signed TLS.
- Token: `~/.config/coolercontrol-api/token` (mode 600). **Never print, echo or paste the token.** Use the helper, which reads it itself.
- If calls return 401, the token was revoked: ask the user to create a new access token in CoolerControl settings and write it into the token file themselves (e.g. `nano ~/.config/coolercontrol-api/token`). Don't ask them to paste it in chat.

## Helper: `~/.claude/skills/cooling/ccapi.py`
```
ccapi.py status                    # temps + fan duty/RPM per device (labelled)
ccapi.py backup                    # save profiles+functions to ~/.config/coolercontrol-api/backups/
ccapi.py get /profiles             # also /functions, /devices, /settings, /devices/<uid>/settings
ccapi.py put  <path> '<json>'      # or @file.json
ccapi.py post <path> '<json>'
ccapi.py delete <path>
```

## API calls known to work (v4.3.1)
- Update a profile: `PUT /profiles` with the **full** profile object (GET it first, modify, send back).
- Create a profile or function: `POST /profiles` / `POST /functions` with a client-generated `uid` (`uuidgen`) and all fields (copy the shape from an existing one).
- Delete: `DELETE /profiles/<uid>`, `DELETE /functions/<uid>`.
- Assign a profile to a fan: `PUT /devices/<device_uid>/settings/<channel>/profile` with body `{"profile_uid": "<uid>"}`.
- Lighting (not used, see OpenRGB note below): `PUT /devices/<uid>/settings/<channel>/lighting`; clear a channel with `PUT .../settings/<channel>/reset` body `{}`. Disable a device: `PUT /settings/devices/<uid>` with its full object and `"disable": true`.
- Live readings: `POST /status` with body `{}`.
- Changes persist to `/etc/coolercontrol/config.toml` automatically.

## Hardware and current setup (as of 2026-11-14; verify with `get` before relying on it)
| Device | UID | Notes |
|---|---|---|
| RTX 2070 Super | `04e313c684cd1ba4df7c059652a801c7d7355d62a4491732f7e02c348e471e42` | channel `fan1`; temps `GPU Temp`, `GPU Temp Hotspot`. Firmware target 83°C: above that the card's firmware takes over the fan (reads 120–128%). |
| Ryzen 7 3700X | `ad4ed06b2d5d12de6c343c5d90f1fafee5e2cc4c1be6d513608d22dcf10131ad` | temps `temp1` = Tctl, `temp3` = Tccd1. Readings jump quickly, so give curves that use it a smoothing function. |
| NZXT Smart Device V2 | `4b9cd1bc5fb2921253e6b7dd5b1b011086ea529d915a86b3560c236084452807` | case fans on `fan2`, `fan3`. `fan1` is an unused port: ignore it. LEDs controlled by OpenRGB, not CoolerControl. |
| Gigabyte RGB Fusion 2.0 8297 | `6652394d0545f0577cc613773ca85145b28fb5a266512af9e414704d3ed10744` | motherboard RGB. **Disabled in CoolerControl**; OpenRGB controls it. |
| AMD Wraith Prism (CPU cooler RGB) | USB `2516:0051` | Not supported by liquidctl/CoolerControl. Controlled by OpenRGB over USB. |
| RAM RGB | SMBus `i2c-7` 0x5A/0x5B | Kernel option `acpi_enforce_resources=lax` added 2026-11-14 (GRUB backup at `/etc/default/grub.bak`), so the PIIX4 SMBus is exposed. OpenRGB controls the RAM (detected as "Corsair Dominator Platinum", Direct mode only). `jc42` hwmon now gives DIMM temps. |
| it8792 | `261622c9…` | secondary motherboard chip, nothing connected. The CPU cooler and motherboard fan headers are on the IT8688E, which Linux doesn't detect (ACPI resource conflict), so they're BIOS-controlled. Since 2026-11-14 the ACPI conflict is worked around (`acpi_enforce_resources=lax`), but the kernel's built-in `it87` driver doesn't support the IT8688E, so it still isn't detected. Controlling it would need the out-of-tree it87 driver (frankcrawford/it87, via DKMS); the user hasn't decided. |

Lighting: **all lighting is handled by the `/lighting` skill (OpenRGB), not CoolerControl.** Don't set lighting through this API (it would fight OpenRGB). CoolerControl has no lighting settings, and the Gigabyte RGB controller is disabled in CoolerControl.

Profiles:
- **My Profile** (`0840dd7f-04cb-4c72-9303-4d78f0e92a55`): Graph on GPU Temp, drives the GPU `fan1`. Curve `[[0,30],[40,30],[60,45],[70,60],[78,80],[83,100],[110,100]]`, function "My Function" (`02ba5ea0-…`). Keep the minimum at or above 30%. Gaming result: ~63–64°C at ~50% fan.
- **Case Fans** (`0d81f0cd-f2ba-4bd9-9369-6c06e17ff345`): Mix, `Max` of the two curves below, drives NZXT `fan2` and `fan3`.
  - **Case - CPU curve** (`e72c64e1-a35e-4f50-b5a0-45f874e752ad`): Tctl, `[[0,35],[50,35],[70,50],[80,70],[90,100],[100,100]]`
  - **Case - GPU curve** (`27a29df1-8593-4caa-832e-b64b54112847`): GPU Temp, `[[0,35],[45,35],[60,50],[70,65],[80,100],[110,100]]`
  - Both use the function **Case Smooth** (`c1c2ec3b-e127-4d9a-a244-971d4632ae62`): response_delay 3, deviance 3.

## Procedure for any change
1. `ccapi.py backup` first.
2. GET the current object, change only what's needed, PUT/POST it back. Check that the HTTP status is 200.
3. Verify: run `ccapi.py status` a few times (sleep about 3s between runs) and confirm the fan duty follows the curve. For the GPU you can also use `nvidia-smi --query-gpu=temperature.gpu,fan.speed,utilization.gpu --format=csv`.
4. If the user is gaming, a 2–3 minute `nvidia-smi ... -l 1` recording shows where temperatures settle. Watch `clocks_throttle_reasons.active` (0x20 or 0x40 means a heat-related slowdown).
5. Report the before and after state to the user, and update the "Hardware and current setup" section of this file if profiles or UIDs changed.

Safety: never set a GPU curve that lets the card reach 83°C under load, never set fans to 0% (stalled fans may not restart), and don't touch device settings for hardware not listed above without asking.
