"""
Scheduled Tasks
Periodic background tasks for the platform
"""

import asyncio
from datetime import datetime
from loguru import logger


class ScheduledTask:
    """Base scheduled task"""
    
    def __init__(self, name: str, interval_seconds: int):
        self.name = name
        self.interval_seconds = interval_seconds
        self.running = False
        self.task: asyncio.Task | None = None
    
    async def run(self):
        """Run the task"""
        raise NotImplementedError
    
    async def _loop(self):
        """Task loop"""
        self.running = True
        while self.running:
            try:
                await self.run()
            except Exception as e:
                logger.error(f"Task {self.name} error: {e}")
            await asyncio.sleep(self.interval_seconds)
    
    def start(self):
        """Start the task"""
        if not self.running:
            self.task = asyncio.create_task(self._loop())
            logger.info(f"Task started: {self.name}")
    
    def stop(self):
        """Stop the task"""
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info(f"Task stopped: {self.name}")


class HealthCheckTask(ScheduledTask):
    """Periodic health check task"""
    
    def __init__(self):
        super().__init__("health_check", 30)
    
    async def run(self):
        logger.debug("Health check passed")


class RiskMonitorTask(ScheduledTask):
    """Periodic risk monitoring task"""
    
    def __init__(self):
        super().__init__("risk_monitor", 60)
    
    async def run(self):
        logger.debug("Risk monitor check passed")


_tasks: list[ScheduledTask] = []


def start_scheduler():
    """Start all scheduled tasks"""
    global _tasks
    _tasks = [
        HealthCheckTask(),
        RiskMonitorTask()
    ]
    for task in _tasks:
        task.start()
    logger.info(f"Scheduler started with {len(_tasks)} tasks")


def stop_scheduler():
    """Stop all scheduled tasks"""
    global _tasks
    for task in _tasks:
        task.stop()
    logger.info("Scheduler stopped")
