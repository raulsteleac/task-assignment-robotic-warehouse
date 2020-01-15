import gym
from .warehouse import Warehouse, RewardType, Action
import itertools

_perms = itertools.product(
    range(1, 5), range(3, 10, 2), range(20), range(20), ["indiv", "global", "twostage"]
)
_rewards = {
    "indiv": RewardType.INDIVIDUAL,
    "global": RewardType.GLOBAL,
    "twostage": RewardType.TWO_STAGE,
}

for rows, cols, agents, req, rew in _perms:
    gym.register(
        id=f"rware-{rows}x{cols}-{agents}ag-{req}req-{rew}-v0",
        entry_point="robotic_warehouse.warehouse:Warehouse",
        kwargs={
            "column_height": 8,
            "shelf_rows": rows,
            "shelf_columns": cols,
            "n_agents": agents,
            "msg_bits": 0,
            "sensor_range": 1,
            "request_queue_size": req,
            "max_inactivity_steps": None,
            "max_steps": 500,
            "reward_type": _rewards[rew],
        },
    )
