import asyncio
import importlib.util
import json
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
MmuAceTool = mmu_ace.MmuAceTool
MmuAcePatcher = mmu_ace.MmuAcePatcher


class StubPrinter:
    async def send_request(self, method: str, params: dict):  # pragma: no cover - interface stub
        raise RuntimeError("unexpected call")


class StubServer:
    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def send_event(self, name: str, payload: dict):
        self.events.append((name, payload))


def _build_controller(tool_count: int = 2) -> MmuAceController:
    controller = object.__new__(MmuAceController)
    controller.printer = StubPrinter()
    controller.server = StubServer()
    controller.ace = MmuAce()

    controller.ace.tools = [MmuAceTool() for _ in range(tool_count)]
    controller.ace.ttg_map = list(range(tool_count))

    return controller


def _build_patcher(controller: MmuAceController) -> MmuAcePatcher:
    patcher = object.__new__(MmuAcePatcher)
    patcher.ace_controller = controller
    return patcher


def test_on_gcode_mmu_slicer_tool_map_parses_csv_payload():
    controller = _build_controller()
    patcher = _build_patcher(controller)

    asyncio.run(patcher._on_gcode_mmu_slicer_tool_map({"MAP": "0:1,1:0"}, None))

    assert controller.ace.ttg_map == [1, 0]
    assert [tool.gate_index for tool in controller.ace.tools] == [1, 0]

    assert controller.server.events, "status update should be emitted"
    event_name, payload = controller.server.events[-1]
    assert event_name == "mmu_ace:status_update"
    assert payload["mmu"]["ttg_map"] == [1, 0]


def test_on_gcode_mmu_slicer_tool_map_parses_json_payload():
    controller = _build_controller(tool_count=1)
    patcher = _build_patcher(controller)

    payload = {
        "tools": [
            {"tool": 0, "gate": 2, "name": "PLA Matte", "material": "PLA", "temp": 210},
            {"index": 1, "slot": 3, "material": "PETG", "temperature": 240}
        ]
    }

    asyncio.run(patcher._on_gcode_mmu_slicer_tool_map({"MAP": json.dumps(payload)}, None))

    assert controller.ace.ttg_map == [2, 3]
    assert len(controller.ace.tools) == 2
    assert controller.ace.tools[0].gate_index == 2
    assert controller.ace.tools[0].name == "PLA Matte"
    assert controller.ace.tools[0].material == "PLA"
    assert controller.ace.tools[0].temp == 210
    assert controller.ace.tools[1].gate_index == 3
    assert controller.ace.tools[1].material == "PETG"
    assert controller.ace.tools[1].temp == 240

    event_name, payload = controller.server.events[-1]
    assert event_name == "mmu_ace:status_update"
    slicer_map = payload["mmu"]["slicer_tool_map"]["tools"]
    assert slicer_map[0]["name"] == "PLA Matte"
    assert slicer_map[1]["material"] == "PETG"


@pytest.mark.parametrize("map_value", ["", "foo", "0-"])
def test_on_gcode_mmu_slicer_tool_map_rejects_invalid_payload(map_value: str):
    controller = _build_controller()
    patcher = _build_patcher(controller)

    with pytest.raises(ValueError):
        asyncio.run(patcher._on_gcode_mmu_slicer_tool_map({"MAP": map_value}, None))

    assert controller.ace.ttg_map == [0, 1]
    assert controller.server.events == []
