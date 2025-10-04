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
MmuAceTool = mmu_ace.MmuAceTool
MmuAceUnit = mmu_ace.MmuAceUnit
MmuAcePatcher = mmu_ace.MmuAcePatcher
TOOL_GATE_UNKNOWN = mmu_ace.TOOL_GATE_UNKNOWN


class StubPrinter:
    def __init__(self, result="ok", exception: Exception | None = None):
        self.result = result
        self.exception = exception
        self.requests: list[tuple[str, dict]] = []

    async def send_request(self, method: str, params: dict):
        self.requests.append((method, params))
        if self.exception is not None:
            raise self.exception
        return self.result


class StubServer:
    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def send_event(self, name: str, payload: dict):
        self.events.append((name, payload))


def _build_controller() -> MmuAceController:
    controller = object.__new__(MmuAceController)
    controller.printer = StubPrinter()
    controller.server = StubServer()
    controller.ace = MmuAce()

    unit = MmuAceUnit(0, "ACE 1")
    for index, gate in enumerate(unit.gates):
        gate.index = index
    controller.ace.units = [unit]

    tool0 = MmuAceTool()
    tool0.gate_index = 0
    tool1 = MmuAceTool()
    tool1.gate_index = 1
    controller.ace.tools = [tool0, tool1]
    controller.ace.ttg_map = [0, 1]

    return controller


def test_select_tool_updates_state_and_emits_status():
    controller = _build_controller()

    asyncio.run(controller.select_tool(tool=1, gate=1, unit=0))

    assert controller.printer.requests == [
        ("filament_hub/select_tool", {"tool": 1, "index": 1, "id": 0})
    ]
    assert controller.ace.tool == 1
    assert controller.ace.gate == 1
    assert controller.ace.unit == 0
    assert controller.ace.active_filament.tool == 1
    assert controller.ace.active_filament.gate == 1
    assert controller.ace.active_filament.unit == 0
    assert controller.ace.active_filament.empty == "0"
    assert controller.ace.active_filament.status == mmu_ace.ACTION_SELECTING

    assert controller.server.events, "status update should be emitted"
    event_name, payload = controller.server.events[-1]
    assert event_name == "mmu_ace:status_update"
    assert payload["mmu"]["tool"] == 1


def test_select_tool_raises_on_rpc_failure():
    controller = _build_controller()
    controller.printer = StubPrinter(result="error")

    with pytest.raises(RuntimeError):
        asyncio.run(controller.select_tool(tool=0, gate=0, unit=0))

    assert controller.ace.tool == TOOL_GATE_UNKNOWN
    assert controller.server.events == []


class RecordingController:
    def __init__(self):
        self.calls: list[dict[str, int | None]] = []
        self.ace = MmuAce()
        unit = MmuAceUnit(0, "ACE 1")
        for index, gate in enumerate(unit.gates):
            gate.index = index
        self.ace.units = [unit]

        tool0 = MmuAceTool()
        tool0.gate_index = 0
        tool1 = MmuAceTool()
        tool1.gate_index = 1
        self.ace.tools = [tool0, tool1]
        self.ace.ttg_map = [0, 1]

    async def select_tool(self, *, tool: int | None, gate: int | None, unit: int | None):
        self.calls.append({"tool": tool, "gate": gate, "unit": unit})

    def _resolve_gate(self, gate_index: int):
        for unit in self.ace.units:
            for gate in unit.gates:
                if gate.index == gate_index:
                    return unit, gate
        return None, None


def test_on_gcode_mmu_select_infers_gate_and_unit_from_tool():
    patcher = object.__new__(MmuAcePatcher)
    controller = RecordingController()
    patcher.ace_controller = controller

    asyncio.run(patcher._on_gcode_mmu_select({"TOOL": "1"}, None))

    assert controller.calls == [{"tool": 1, "gate": 1, "unit": 0}]


def test_on_gcode_mmu_select_accepts_vendor_arguments():
    patcher = object.__new__(MmuAcePatcher)
    controller = RecordingController()
    patcher.ace_controller = controller

    asyncio.run(patcher._on_gcode_mmu_select({"UNIT": "0", "GATE": "1"}, None))

    assert controller.calls[-1] == {"tool": 1, "gate": 1, "unit": 0}


def test_on_gcode_mmu_select_rejects_invalid_numbers():
    patcher = object.__new__(MmuAcePatcher)
    patcher.ace_controller = RecordingController()

    with pytest.raises(ValueError):
        asyncio.run(patcher._on_gcode_mmu_select({"TOOL": "foo"}, None))


class FailingController(RecordingController):
    async def select_tool(self, *, tool: int | None, gate: int | None, unit: int | None):
        raise RuntimeError("rpc failed")


def test_on_gcode_mmu_select_propagates_controller_errors():
    patcher = object.__new__(MmuAcePatcher)
    controller = FailingController()
    patcher.ace_controller = controller

    with pytest.raises(RuntimeError):
        asyncio.run(patcher._on_gcode_mmu_select({"GATE": "0"}, None))

    assert controller.calls == []
