# strategy.py
import math
from typing import List, Tuple, Dict
import numpy as np

Point = Tuple[float, float]

def euclid(a: Point, b: Point) -> float:
    return math.hypot(a[0]-b[0], a[1]-b[1])

def compute_strategy(
    start: Point,
    artifact_positions: List[Point],
    params: Dict
) -> Dict:
    """
    Simple greedy strategy:
    - Robot starts at `start`.
    - Visits closest artifact next (nearest neighbor) while time allows.
    - Travel time = distance / speed.
    - Pickup time = params['pickup_time'] (per artifact).
    - Autonomous window grants autonomous_multiplier on points for items collected during auto_time.
    - Some zones (decode_zone) give extra bonus points per artifact if collected inside.
    Returns plan with visited order, times, and expected score.
    """
    speed = params.get("robot_speed", 100.0)  # units per second (field units / s)
    pickup_time = params.get("pickup_time", 3.0)  # seconds to pick one artifact
    total_time = params.get("match_time", 150.0)  # total match time seconds
    auton_time = params.get("auton_time", 30.0)
    points_per_artifact = params.get("points_per_artifact", 5)
    decode_zone = params.get("decode_zone", ((450, 100), 80))  # center, radius
    decode_bonus = params.get("decode_bonus", 3)  # extra points if inside zone
    auton_multiplier = params.get("auton_multiplier", 1.5)

    remaining_time = total_time
    t = 0.0
    pos = start
    visited = []
    score = 0.0

    # copy of artifacts
    artifacts = artifact_positions.copy()
    # greedy nearest-first
    while artifacts:
        # find nearest artifact
        dlist = [(euclid(pos, a), a) for a in artifacts]
        dlist.sort(key=lambda x: x[0])
        d, target = dlist[0]
        travel_time = d / speed
        time_needed = travel_time + pickup_time

        if t + time_needed > total_time:
            break  # no time to go and pick next artifact

        # move to target
        t += travel_time
        # determine if in auton window for pickup
        in_auton = t <= auton_time
        # pickup
        t += pickup_time

        # scoring
        base = points_per_artifact
        bonus = 0
        # decode zone check
        center, radius = decode_zone
        if euclid(target, center) <= radius:
            bonus += decode_bonus

        gained = base + bonus
        if in_auton:
            gained *= auton_multiplier

        score += gained

        visited.append({
            "pos": target,
            "travel_time": travel_time,
            "pickup_time": pickup_time,
            "time_at_pickup": t,
            "in_auton": in_auton,
            "base_points": base,
            "bonus_points": bonus,
            "gained": gained
        })

        pos = target
        artifacts.remove(target)

    # final return to start is optional; we compute total used time
    used_time = t
    return {
        "visited": visited,
        "expected_score": score,
        "used_time": used_time,
        "remaining_artifacts": len(artifacts),
        "params": params
    }

# helper to produce some fixed layout artifacts (reproducible)
def default_field_layout() -> Dict:
    """
    Returns:
      - start position
      - list of artifact positions
      - decode zone definition (center, radius)
      Coordinates are in arbitrary field units (0..600 x, 0..400 y)
    """
    start = (50, 200)
    artifacts = [
        (200, 80), (250, 160), (300, 240), (220, 320),
        (420, 90), (470, 160), (520, 220), (430, 300)
    ]
    decode_zone = ((470, 160), 70)  # approx where decode zone sits
    return {"start": start, "artifacts": artifacts, "decode_zone": decode_zone}
