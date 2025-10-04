import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "files/4-apps/home/rinkhals/apps/40-moonraker/mmu_ace.py"

spec = importlib.util.spec_from_file_location("mmu_ace_module", MODULE_PATH)
mmu_ace = importlib.util.module_from_spec(spec)
mmu_ace.TOOL_GATE_UNKNOWN = -1
sys.modules[spec.name] = mmu_ace
assert spec.loader is not None
spec.loader.exec_module(mmu_ace)


MmuAceController = mmu_ace.MmuAceController
MmuAce = mmu_ace.MmuAce
MmuAcePatcher = mmu_ace.MmuAcePatcher


class StubPrinter:
    def __init__(self):
        self.requests: list[tuple[str, dict]] = []

    async def send_request(self, method: str, params: dict):
        self.requests.append((method, params))
        return "ok"


class StubServer:
    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def send_event(self, name: str, payload: dict):
        self.events.append((name, payload))


class StubAceController:
    def __init__(self):
        self.updated_groups: list[int] | None = None

    async def update_endless_spool_groups(self, groups: list[int]):
        self.updated_groups = groups


def test_update_endless_spool_groups_sends_rpc_and_updates_state():
    controller = object.__new__(MmuAceController)
    controller.printer = StubPrinter()
    controller.server = StubServer()
    controller.ace = MmuAce()

    asyncio.run(controller.update_endless_spool_groups([0, 2, 3]))

    assert controller.printer.requests == [
        ("filament_hub/set_endless_spool_groups", {"groups": [0, 2, 3]})
    ]
    assert controller.ace.endless_spool_groups == [0, 2, 3]
    assert controller.server.events, "status update should be emitted"
    event_name, payload = controller.server.events[-1]
    assert event_name == "mmu_ace:status_update"
    assert payload["mmu"]["endless_spool_groups"] == [0, 2, 3]


@pytest.mark.parametrize("argument,expected", [
    ("[0, 1, 2]", [0, 1, 2]),
    ("0,1,2", [0, 1, 2])
])
def test_on_gcode_endless_spool_parses_groups(argument: str, expected: list[int]):
    patcher = object.__new__(MmuAcePatcher)
    patcher.ace_controller = StubAceController()

    asyncio.run(patcher._on_gcode_mmu_endless_spool({"GROUPS": argument}, None))

    assert patcher.ace_controller.updated_groups == expected


def test_on_gcode_endless_spool_rejects_invalid_groups():
    patcher = object.__new__(MmuAcePatcher)
    patcher.ace_controller = StubAceController()

    with pytest.raises(ValueError):
        asyncio.run(patcher._on_gcode_mmu_endless_spool({"GROUPS": "0,foo"}, None))

    assert patcher.ace_controller.updated_groups is None
