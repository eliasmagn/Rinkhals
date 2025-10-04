---
title: Home
weight: 3
---

# Firmware documentation overview

This section collects the research that keeps Rinkhals aligned with Anycubic's Kobra-series firmware. Use it as a map before diving into the deeper analyses—each topic below links to the authoritative reference for that slice of the platform.

## Supported firmware releases

Rinkhals tracks the two most recent Anycubic firmware releases for each supported printer whenever possible. Firmware that falls outside that window may still function, but new capabilities and fixes are only validated against the versions listed in the [project README](../../../README.md#rinkhals-installation). When experimenting with older builds, review the release notes and confirm bootloader compatibility before flashing.

## Start here

- **Boot flow & runtime services** — Follow the startup chain from the Rockchip init scripts through Rinkhals' own entrypoint in [File structure](./file-structure.md#kobra-startup-sequence). The same document outlines how Rinkhals layers its overlay filesystem and supervises vendor daemons.
- **Partition layout & storage strategy** — The A/B partition map, user storage volumes, and overlay mounts described in [File structure](./file-structure.md#partitions) explain how updates are staged and how recovery works.
- **GoKlipper integration notes** — Rinkhals keeps Anycubic's Go-based Klipper fork in place; [GoKlipper integration](./goklipper.md) summarizes what the vendor binaries provide and how Rinkhals hooks in without breaking stock features.

## Key analyses

### Boot flow deep dive
- [File structure](./file-structure.md) walks through `/etc/init.d/rcS`, the chained launchers under `/userdata/app`, and the safeguards that restart Anycubic services if Rinkhals fails.
- [Binary decompilation & patching](./binary-decompilation-and-patching.md) highlights the UI patches and injected entry points that make the Rinkhals touch interface appear alongside the factory menus.

### Partitioning and persistence
- [File structure](./file-structure.md#partitions) documents each eMMC slice, including the paired `system`, `oem`, and `ac_*` partitions that Rinkhals swaps during upgrades.
- [Vanilla Klipper coexistence](./vanilla-klipper.md) explains how community configurations can be staged without corrupting Anycubic's persistent data or breaking the A/B update flow.

### Update & IPC pathways
- [File structure](./file-structure.md#rinkhals-startup-sequence) covers how OTA packages are validated and mounted before Rinkhals hands control back to vendor processes.
- [MQTT topics](./mqtt.md) and [IPC command reference](./ipc-commands.md) catalogue the channels Rinkhals monitors to track update status, trigger maintenance, and patch telemetry into Moonraker.
- [MMU Ace bridge](./mmu-ace.md) details the synchronized update events flowing between Anycubic's firmware and Moonraker for multi-material hardware.

## Warnings & best practices

> [!WARNING]
> Flashing or patching outside the documented workflows can soft-brick the printer. Always verify firmware compatibility, keep a recovery USB handy, and avoid cross-flashing files meant for different Kobra models.

> [!IMPORTANT]
> The dual-partition layout assumes clean fallbacks. Do not modify `/system_*`, `/oem_*`, or `/ac_*` directly—stage customizations through `/useremain/rinkhals/[VERSION]` or the documented app system so you can roll back safely.

> [!TIP]
> Capture the contents of `/userdata` before experimenting. Logs from `/useremain/rinkhals/logs` and MQTT traces often make the difference when diagnosing update issues.

## Additional references

- [Binary decompilation & patching](./binary-decompilation-and-patching.md) — UI hooks and binary instrumentation strategies.
- [GoKlipper integration](./goklipper.md) — How Anycubic's Go-based stack interacts with upstream Klipper.
- [IPC command reference](./ipc-commands.md) — Internal RPCs exposed by vendor binaries.
- [MQTT topics](./mqtt.md) — Broker subjects published by Anycubic services.
- [MMU Ace bridge](./mmu-ace.md) — Detailed MMU event and command mapping.
- [Vanilla Klipper coexistence](./vanilla-klipper.md) — Guidelines for running community configs alongside Rinkhals.

Use this index as your launchpad when updating or reverse-engineering the platform. If you discover discrepancies, annotate the relevant page so the rest of the ecosystem stays in sync.
