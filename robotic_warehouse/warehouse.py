import logging

import gym
from gym import spaces

from ma_gym.envs.utils.action_space import MultiAgentActionSpace
from ma_gym.envs.utils.observation_space import MultiAgentObservationSpace

from enum import Enum
import numpy as np

_AXIS_Z = 0
_AXIS_Y = 1
_AXIS_X = 2

_COLLISION_LAYERS = 2

_LAYER_AGENTS = 0
_LAYER_SHELFS = 1


class Action(Enum):
    NOOP = 0
    FORWARD = 1
    LEFT = 2
    RIGHT = 3
    LOAD = 4
    UNLOAD = 5


class Direction(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


class Entity:
    def __init__(self, id_: int, x: int, y: int):
        self.id = id_
        self.x = x
        self.y = y


class Agent(Entity):
    counter = 0

    def __init__(self, x: int, y: int, dir_: Direction, msg_bits: int):
        Agent.counter += 1
        super().__init__(Agent.counter, x, y)
        self.dir = dir_
        self.message = np.zeros(msg_bits)

    @property
    def collision_layers(self):
        if self.loaded:
            return (_LAYER_AGENTS, _LAYER_SHELFS)
        else:
            return (_LAYER_AGENTS,)


class Shelf(Entity):
    counter = 0

    def __init__(self, x, y):
        Shelf.counter += 1
        super().__init__(Shelf.counter, x, y)

    @property
    def collision_layers(self):
        return (_LAYER_SHELFS,)


class _VectorWriter:
    def __init__(self, size: int):
        self.vector = np.zeros(size)
        self.idx = 0

    def write(self, data):
        data_size = len(data)
        self.vector[self.idx : self.idx + data_size] = data
        self.idx += data_size

    def skip(self, bits):
        self.idx += bits


class Warehouse(gym.Env):

    metadata = {"render.modes": ["human", "rgb_array"]}

    def __init__(self):
        self.grid_size = (29, 10)

        self.n_agents = 20
        self._max_steps = None
        self.n_shelfs = 20
        self.msg_bits = 2

        self.grid = np.zeros((_COLLISION_LAYERS, *self.grid_size), dtype=np.int32)

        self.action_space = MultiAgentActionSpace(
            [spaces.Discrete(len(Action)) for _ in range(self.n_agents)]
        )

        self.sensor_range = 1
        # self.observation_space = MultiAgentObservationSpace(
        #     [spaces.Box(self._obs_low, self._obs_high) for _ in range(self.n_agents)]
        # )

    def _is_highway(self, x: int, y: int) -> bool:
        return (
            (x % 3 == 0)  # vertical highways
            or (y % 9 == 0)  # horizontal highways
            or (y == self.grid_size[0] - 1)  # delivery row
            or (  # remove a box for queuing
                (y > self.grid_size[0] - 11)
                and ((x == self.grid_size[1] // 2 - 1) or (x == self.grid_size[1] // 2))
            )
        )

    def _make_obs(self, agent):
        obs = [agent.x, agent.y]

        min_x = max(0, agent.x - self.sensor_range)
        max_x = min(self.grid_size[1], agent.x + self.sensor_range + 1)

        min_y = max(0, agent.y - self.sensor_range)
        max_y = min(self.grid_size[0], agent.y + self.sensor_range + 1)

        shelfs = self.grid[_LAYER_SHELFS, min_y:max_y, min_x:max_x]

        # find neighboring agents
        agents = self.grid[_LAYER_AGENTS, min_y:max_y, min_x:max_x].reshape(-1)
        # agents = agents[np.nonzero(agents)]
        # agents = agents[agents != agent.id]
        # agents = agents - 1  # to get indices to self.agents
        # agents = list(agents)

        bits_per_agent = len(Direction) + self.msg_bits

        agent_obs = _VectorWriter(bits_per_agent * len(agents))
        print(bits_per_agent * len(agents))
        print(len(agents))

        for i, id_ in enumerate(agents):
            if id_ == 0 or id_ == agent.id:
                agent_obs.skip(bits_per_agent)

            agent_obs.write(np.eye(len(Direction))[self.agents[id_ - 1].dir])
            agent_obs.write(self.agents[id_ - 1].message)

        agent_obs = _VectorWriter.vector
        print(agent.id, agents_obs)

        # get neighbors:

    def reset(self):
        Shelf.counter = 0
        Agent.counter = 0

        # n_xshelf = (self.grid_size[1] - 1) // 3
        # n_yshelf = (self.grid_size[0] - 2) // 9

        # make the shelfs
        self.shelfs = [
            Shelf(x, y)
            for y, x in zip(
                np.indices(self.grid_size)[0].reshape(-1),
                np.indices(self.grid_size)[1].reshape(-1),
            )
            if not self._is_highway(x, y)
        ]

        # spawn agents at random locations
        agent_locs = np.random.choice(
            np.arange(self.grid_size[0] * self.grid_size[1]),
            size=self.n_agents,
            replace=False,
        )
        agent_locs = np.unravel_index(agent_locs, self.grid_size)
        # and direction
        agent_dirs = np.random.choice(4, size=self.n_agents)

        self.agents = [
            Agent(x, y, dir_, self.msg_bits)
            for y, x, dir_ in zip(*agent_locs, agent_dirs)
        ]

        for s in self.shelfs:
            self.grid[_LAYER_SHELFS, s.y, s.x] = s.id

        for a in self.agents:
            self.grid[_LAYER_AGENTS, a.y, a.x] = a.id
        print(self.grid)

        return [self._make_obs(agent) for agent in self.agents]
        # for s in self.shelfs:
        #     self.grid[0, s.y, s.x] = 1
        # print(self.grid[0])

    def step(self, actions):
        ...

    def render(self, mode="human"):
        ...

    def close(self):
        ...

    def seed(self, seed=None):
        ...


if __name__ == "__main__":
    env = Warehouse()
    env.reset()
