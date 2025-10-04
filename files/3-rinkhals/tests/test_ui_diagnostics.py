import builtins
import importlib.util
import sys
import types
import uuid
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "opt/rinkhals/ui/common.py"


def load_ui_common(monkeypatch: pytest.MonkeyPatch):
    module_name = f"ui_common_for_test_{uuid.uuid4().hex}"

    lv_helpers = types.SimpleNamespace(
        is_windows=lambda: False,
        is_linux=lambda: False,
    )
    lv_stub = types.SimpleNamespace(helpers=lv_helpers)

    monkeypatch.setitem(sys.modules, "lvgl", lv_stub)
    monkeypatch.setitem(sys.modules, "lvgl_rinkhals", types.SimpleNamespace())

    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def has_custom_cfg_warning(
    module,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    content: str,
) -> bool:
    custom_cfg_path = "/useremain/home/rinkhals/printer_data/config/printer.custom.cfg"
    custom_cfg_file = tmp_path / "printer.custom.cfg"
    custom_cfg_file.write_text(content)

    def fake_exists(path: str) -> bool:
        if path in {
            custom_cfg_path,
            "/userdata/app/gk/printer.cfg",
            "/userdata/app/gk/config/api.cfg",
        }:
            return True
        return False

    monkeypatch.setattr(module.os.path, "exists", fake_exists)
    monkeypatch.setattr(module.os.path, "getmtime", lambda path: 0)
    monkeypatch.setattr(module, "hash_md5", lambda path: "hash")
    monkeypatch.setattr(
        module.PrinterInfo,
        "get",
        staticmethod(lambda: types.SimpleNamespace(model_code="K3")),
    )
    monkeypatch.setattr(
        module.Firmware,
        "get_current_version",
        staticmethod(lambda: "2.3.3.2"),
    )

    real_open = builtins.open

    def fake_open(path, mode="r", *args, **kwargs):
        if path in {
            custom_cfg_path,
            "/userdata/app/gk/printer.cfg",
            "/userdata/app/gk/config/api.cfg",
        }:
            return real_open(custom_cfg_file, mode, *args, **kwargs)
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    diagnostics = list(module.Diagnostic.collect())
    return any(d.short_text == "Customized configuration" for d in diagnostics)


def test_printer_custom_cfg_only_comments_does_not_warn(monkeypatch, tmp_path):
    module = load_ui_common(monkeypatch)

    warned = has_custom_cfg_warning(
        module,
        monkeypatch,
        tmp_path,
        "# custom tweaks documented\n\n   # and spaces\n",
    )

    assert not warned


def test_printer_custom_cfg_with_settings_triggers_warning(monkeypatch, tmp_path):
    module = load_ui_common(monkeypatch)

    warned = has_custom_cfg_warning(
        module,
        monkeypatch,
        tmp_path,
        "[heater_bed]\nmax_temp = 120\n",
    )

    assert warned
