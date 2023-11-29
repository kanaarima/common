
from ..database.objects import DBScore
from datetime import datetime

import hashlib

def compute_score_checksum(score: DBScore) -> str:
    return hashlib.md5(
        f'{score.n100 + score.n300}p{score.n50}o{score.nGeki}o{score.nKatu}t{score.nMiss}a{score.beatmap.md5}r{score.max_combo}e{score.perfect}y{score.user.name}o{score.total_score}u{score.grade}{score.mods}{not score.failtime}'.encode()
    ).hexdigest()

def get_ticks(dt: datetime) -> int:
    dt = dt.replace(tzinfo=None)
    return int((dt - datetime(1, 1, 1)).total_seconds() * 10000000)
