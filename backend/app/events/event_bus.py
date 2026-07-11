"""
Asynchronous in-process Event Bus.
Decouples publishing modules from subscribing modules via an async queue dispatcher.
"""

import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Union
from loguru import logger

from app.events.base_event import BaseEvent


class EventBus:
    """
    Publish-Subscribe event router executing asynchronously.
    Maintains subscriber lists and dispatches events concurrently from an internal queue.
    """
    def __init__(self) -> None:
        # Maps event name to a list of handler coroutine functions
        self._subscribers: Dict[str, List[Callable[[BaseEvent], Coroutine[Any, Any, None]]]] = {}
        # Decouples publishing threads/tasks from subscriber execution
        self._queue: asyncio.Queue[BaseEvent] = asyncio.Queue()
        self._dispatch_task: Union[asyncio.Task, None] = None
        self._running: bool = False
        
        # Statistics
        self.published_count: int = 0
        self.failed_count: int = 0

    def subscribe(self, event_name: str, handler: Callable[[BaseEvent], Coroutine[Any, Any, None]]) -> None:
        """
        Registers a handler callback to be invoked when matching events are published.
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)
            logger.info(f"Subscribed handler {handler.__name__} to event: {event_name}")

    def unsubscribe(self, event_name: str, handler: Callable[[BaseEvent], Coroutine[Any, Any, None]]) -> None:
        """
        Removes a handler callback from subscription list.
        """
        if event_name in self._subscribers and handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)
            logger.info(f"Unsubscribed handler {handler.__name__} from event: {event_name}")

    async def publish(self, event: BaseEvent) -> None:
        """
        Pushes an event to the processing queue for asynchronous distribution.
        """
        await self._queue.put(event)
        self.published_count += 1
        logger.debug(f"Event published to EventBus queue: {event.event_name} (ID: {event.event_id})")

    def start(self) -> None:
        """
        Starts the background worker dispatching events from the queue.
        """
        if self._running:
            logger.warning("EventBus dispatch loop is already running.")
            return
        
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())
        logger.info("EventBus async dispatch worker started.")

    async def stop(self) -> None:
        """
        Gracefully terminates the background dispatch loop, draining active items.
        """
        if not self._running:
            logger.warning("EventBus is not running.")
            return

        logger.info("Stopping EventBus dispatch worker...")
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
            self._dispatch_task = None
        logger.info("EventBus dispatch worker stopped.")

    async def _dispatch_loop(self) -> None:
        """
        Long-running loop fetching events from queue and distributing them.
        """
        while self._running:
            try:
                event = await self._queue.get()
                event_name = event.event_name
                handlers = self._subscribers.get(event_name, [])
                
                if handlers:
                    # Concurrently dispatch the event to all subscribers of this event
                    tasks = [self._safe_dispatch(handler, event) for handler in handlers]
                    await asyncio.gather(*tasks)
                
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in EventBus dispatch loop: {e}")

    async def _safe_dispatch(
        self,
        handler: Callable[[BaseEvent], Coroutine[Any, Any, None]],
        event: BaseEvent
    ) -> None:
        """
        Executes a single subscriber handler safely, isolating errors.
        """
        try:
            await handler(event)
        except Exception as e:
            self.failed_count += 1
            logger.error(
                f"Handler {handler.__name__} failed processing event "
                f"{event.event_name} (ID: {event.event_id}): {e}"
            )

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    @property
    def subscriber_count(self) -> int:
        return sum(len(handlers) for handlers in self._subscribers.values())


# Centralized application EventBus singleton
event_bus = EventBus()
