# app/events.py
from asyncio import Queue
from typing import Dict
from datetime import datetime

class EventManager:
    def __init__(self):
        self.listeners: Dict[int, Queue] = {}
        self._counter = 0
        self.event_queue = Queue()

    async def register(self) -> tuple[int, Queue]:
        self._counter += 1
        queue = Queue()
        self.listeners[self._counter] = queue
        return self._counter, queue

    def deregister(self, listener_id: int):
        self.listeners.pop(listener_id, None)

    async def emit(self, event_type: str, book_data: dict):
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "data": book_data
        }
        # Add to event queue and notify all listeners
        await self.event_queue.put(event)
        if self.listeners:
            for queue in self.listeners.values():
                await queue.put(event)

# Create a global event manager instance
event_manager = EventManager()