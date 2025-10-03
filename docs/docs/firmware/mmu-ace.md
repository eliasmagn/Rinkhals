---
title: MMU Ace bridge
---

## Overview

Rinkhals ships a Moonraker component (`mmu_ace.py`) that mirrors the Anycubic ACE firmware state so web UIs can interact with the multi-material unit without bypassing stock services. The bridge now:

- Subscribes to `filament_hub` status updates and publishes them as `mmu_ace:status_update` events.
- Normalizes slot metadata (material, color, spool IDs, RFID state) across one or two ACE hubs.
- Proxies spool edits and dryer commands back to the vendor firmware so Klipper-side tools and the touch UI stay synchronized.

Use the `/server/mmu-ace` endpoint or subscribe to `mmu_ace:status_update` to fetch the full status payload.

## Status payload

The status patcher exposes the following highlights:

- `mmu.gate_status`, `mmu.gate_color`, and `mmu.gate_material` list the consolidated slots across all hubs.
- `mmu.active_filament` reports the currently selected gate, tool index, name, and material.
- `mmu_machine.unit_0` / `unit_1` describe each ACE hub, including the dryer status reported by the firmware.

Clients should treat gate indexes as global; the patcher maps tools to gates even when two hubs are attached.

## Bridge GCodes

### `MMU_GATE_MAP`

Triggered when the UI edits a spool. The `MAP` argument is a JSON-like object whose values include:

| Key | Description |
| --- | --- |
| `status` | Gate state (`0` empty, `1` available, `2` buffer, `-1` unknown). |
| `name` | Display name for the spool/tool. |
| `material` | Material type reported to slicers and Klipper. |
| `color` | Hex string (`RRGGBB` or `RRGGBBAA`) converted to the firmware RGB payload. |
| `temp` | Preferred temperature for the tool. |
| `spool_id` | UI spool identifier (not persisted by the firmware yet, but kept in Moonraker state). |
| `speed_override` | Slot-specific feed override. |
| `sku`, `brand`, `source` | Optional metadata preserved in Moonraker state. |

The bridge forwards the material and color to `filament_hub/set_filament_info` and updates the in-memory model so Moonraker clients immediately reflect the change.

### `MMU_TTG_MAP`

Maps tool indexes to gate indexes. The bridge updates the slicer metadata block (`ams_settings`) so OrcaSlicer/PrusaSlicer color previews match the physical slots.

### `MMU_DRYER`

Provides dryer control without direct IPC calls.

```
MMU_DRYER ACTION=START UNIT=0 TEMP=45 DURATION=240 FAN=0
MMU_DRYER ACTION=STOP UNIT=0
```

`UNIT` matches the ACE hub ID (`filament_hub.filament_hubs[].id`). The command forwards to `filament_hub/start_drying` or `filament_hub/stop_drying` and patches the cached dryer status so UI widgets update immediately.

## Dryer API reminder

The dryer calls map to the following IPC methods:

- `filament_hub/start_drying` – requires `id`, `temp`, `duration`, and optionally `fan_speed`.
- `filament_hub/stop_drying` – requires `id`.

See [IPC commands](./ipc-commands.md) for raw payload examples.

## Multi-hub behaviour

All helpers treat the list of hubs as a single logical array of gates. When two ACE units are connected, gate indexes continue incrementing (0-3 on hub 0, 4-7 on hub 1). Tool-to-gate maps, slicer metadata, and dryer controls all accept the hub ID so the same bridge works for combo kits and future expansions.
