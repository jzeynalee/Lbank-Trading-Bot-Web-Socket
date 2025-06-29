import asyncio
import websockets
import json
from utils.logger import get_logger

logger = get_logger("ws_client")

class WebSocketClient:
    def __init__(self, symbols, on_message_callback):
        self.symbols = symbols
        self.on_message_callback = on_message_callback
        self.url = "wss://www.lbkex.net/ws/V2/"

    async def connect(self):
        try:
            async with websockets.connect(self.url) as ws:
                # Subscribe to all requested symbols
                for symbol in self.symbols:
                    sub_msg = json.dumps({
                        "action": "subscribe",
                        "subscribe": f"ticker.{symbol}"
                    })
                    await ws.send(sub_msg)
                    logger.info(f"[WS] Subscribed to {symbol}")

                logger.info("[WS] Listening for messages...")

                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        await self.on_message_callback(data)
                    except Exception as e:
                        logger.error(f"[WS MESSAGE ERROR] {e}")
                        await asyncio.sleep(3)

        except Exception as e:
            logger.critical(f"[WS CONNECTION FAILED] {e}")
