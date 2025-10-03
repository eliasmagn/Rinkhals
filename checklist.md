# Development Checklist

## Recently Completed
- [x] Merge Moonraker MMU Ace component into the app package
- [x] Wire MMU-specific hooks into `kobra.py` (GCode interception, status/print patchers)
- [x] Update Moonraker launch scripts to deploy the new component and preserve existing debug tools
- [x] Resolve configuration merge conflicts by keeping webcam support while enabling MMU Ace

## Follow-up Tasks
- [ ] Document MMU Ace usage and limitations in the docs site
- [ ] Validate MMU Ace behavior on KS1 hardware (new bed mesh script paths)
- [ ] Expose MMU status telemetry in the UI once upstream support lands
