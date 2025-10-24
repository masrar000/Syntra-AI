import random, time
from typing import Dict, List

AUDIENCES = ["founder", "creative", "ops"]

def simulate_performance(audience: str) -> Dict:
    # Basic realistic ranges, tweak as desired
    base = {
        "founder": (0.28, 0.05, 0.003),
        "creative": (0.34, 0.09, 0.002),
        "ops": (0.30, 0.06, 0.0025)
    }[audience]
    def jitter(mu, spread):
        x = random.gauss(mu, spread)
        return max(0.0, min(1.0, x))

    open_rate = jitter(base[0], 0.04)
    click_rate = jitter(base[1], 0.03)
    unsub_rate = jitter(base[2], 0.001)
    return {
        "ts": int(time.time()),
        "audience": audience,
        "open_rate": round(open_rate, 4),
        "click_rate": round(click_rate, 4),
        "unsub_rate": round(unsub_rate, 4)
    }
