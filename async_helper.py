"""Async helper that works for ALL bot types (handles no-loop errors)."""
import asyncio
import sys
import threading

# A single persistent event loop running in a background thread.
_loop = None
_loop_thread = None
_loop_lock = threading.Lock()


def _get_loop():
    """Get or create a persistent background event loop."""
    global _loop, _loop_thread
    with _loop_lock:
        if _loop is None or not _loop.is_running():
            _loop = asyncio.new_event_loop()
            _loop_thread = threading.Thread(target=_loop.run_forever, daemon=True)
            _loop_thread.start()
            # Wait for loop to start
            while not _loop.is_running():
                pass
        return _loop


def call_analyze(bot, df_window):
    """Call bot.analyze_market safely in a persistent event loop."""
    try:
        result = bot.analyze_market(df_window)
        if hasattr(result, '__await__'):
            # It's a coroutine
            loop = _get_loop()
            future = asyncio.run_coroutine_threadsafe(result, loop)
            return future.result(timeout=30)
        return result
    except Exception:
        return None
