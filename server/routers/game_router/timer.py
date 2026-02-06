"""
Game phase and offset timers. Flat functions; use conM for broadcast.
"""
import asyncio

from ...util import conM


def cancel_phase_timer(game):
    """Cancel the phase timer task if it exists and is running."""
    task = getattr(game, "phase_timer_task", None)
    current_task = asyncio.current_task()
    if task and not task.done() and task is not current_task:
        task.cancel()


async def offset_timer(game):
    """Run offset countdown and broadcast to game."""
    seconds = game.offset_sec
    for i in range(seconds):
        await conM.broadcast_to_game(game.id, {
            "type": "offset_timer",
            "seconds": seconds - i
        })
        await asyncio.sleep(1)
    await conM.broadcast_to_game(game.id, {
        "type": "offset_timer",
        "seconds": 0
    })


async def phase_timer(game):
    """Run phase countdown (broadcast every 10s) and broadcast to game."""
    seconds = game.phase_sec  # 10의 배수
    for i in range(seconds):
        await asyncio.sleep(1)
        if i % 10 == 0:
            await conM.broadcast_to_game(game.id, {
                "type": "phase_timer",
                "seconds": seconds - i
            })
    await conM.broadcast_to_game(game.id, {
        "type": "phase_timer",
        "seconds": 0
    })
