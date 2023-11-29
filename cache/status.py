
from ..constants import ClientStatus, GameMode, Mods
from ..objects import bStatusUpdate

from typing import Optional
from copy import copy

import app

def update(player_id: int, status: bStatusUpdate) -> None:
    status = copy(status)

    status.action = status.action.value
    status.mode = status.mode.value
    status.mods = status.mods.value

    for key, value in status.__dict__.items():
        app.session.redis.hset(
            f'bancho:status:{player_id}',
            key, value
        )

def get(player_id: int) -> Optional[bStatusUpdate]:
    if status := app.session.redis.hgetall(f'bancho:status:{player_id}'):
        return bStatusUpdate(
            action=ClientStatus(int(status[b'action'])),
            mode=GameMode(int(status[b'mode'])),
            mods=Mods(int(status[b'mods'])),
            beatmap_id=int(status[b'beatmap_id']),
            beatmap_checksum=status[b'beatmap_checksum'],
            text=status[b'text'].decode(),
        )
    else:
        return

def delete(player_id: int) -> None:
    app.session.redis.hdel(
        f'bancho:status:{player_id}',
        'action', 'mode', 'mods', 'text', 'beatmap_id', 'beatmap_checksum'
    )

def exists(player_id: int) -> bool:
    return app.session.redis.exists(
        f'bancho:status:{player_id}'
    )
