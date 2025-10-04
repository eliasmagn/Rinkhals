# Development Checklist

## Recently Completed
- [x] Merge Moonraker MMU Ace component into the app package
- [x] Wire MMU-specific hooks into `kobra.py` (GCode interception, status/print patchers)
- [x] Update Moonraker launch scripts to deploy the new component and preserve existing debug tools
- [x] Resolve configuration merge conflicts by keeping webcam support while enabling MMU Ace
- [x] Mirror ACE telemetry into Moonraker events so UI clients receive live slot and dryer updates
- [x] Allow spool metadata edits (color, material, name) to flow back to the firmware through `MMU_GATE_MAP`
- [x] Bridge endless spool group updates through `MMU_ENDLESS_SPOOL` so Moonraker stays in sync with ACE endless-spool setups
- [x] Add dryer control plumbing and documentation via the new `MMU_DRYER` bridge command
- [x] Support multiple ACE hubs when building tool/gate maps and slicer metadata

## Follow-up Tasks
- [ ] Validate dual-hub and dryer flows on physical hardware (KS1 + combo)
- [ ] Coordinate with UI projects to surface the richer MMU Ace status payload
- [ ] Extend docs with troubleshooting guidance once field feedback arrives
