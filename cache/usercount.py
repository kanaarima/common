
import app

def set(count: int) -> None:
    app.session.redis.set(
        'bancho:users',
        max(0, count)
    )

def get() -> int:
    return int(count) if (count := app.session.redis.get('bancho:users')) else 0

def increment(amount: int = 1) -> None:
    set(get() + amount)

def decrement(amount: int = 1) -> None:
    set(get() - amount)
