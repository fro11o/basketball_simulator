import math
import random
import pygame
import copy

class Position:
    def __init__(self, rect, x_offset, y_offset, factor=1):
        """
        Parameters
        ---------
        rect: [x, y, width, height]
            court size
        x_offset: float
            start point x
        y_offset: float
            start point y
        factor: int
            factor of edge of six-direction
        """
        self.rect = rect
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.factor = factor

        def dfs(x, y, pos):
            if ([x, y+2] not in pos and
                    self.virtual_is_in([x, y+2])):
                pos.append([x, y+2])
                dfs(x, y+2, pos)
            if ([x, y-2] not in pos and
                    self.virtual_is_in([x, y-2])):
                pos.append([x, y-2])
                dfs(x, y-2, pos)
            if ([x+1, y-1] not in pos and
                    self.virtual_is_in([x+1, y-1])):
                pos.append([x+1, y-1])
                dfs(x+1, y-1, pos)
            if ([x+1, y+1] not in pos and
                    self.virtual_is_in([x+1, y+1])):
                pos.append([x+1, y+1])
                dfs(x+1, y+1, pos)
            if ([x-1, y+1] not in pos and
                    self.virtual_is_in([x-1, y+1])):
                pos.append([x-1, y+1])
                dfs(x-1, y+1, pos)
            if ([x-1, y-1] not in pos and
                    self.virtual_is_in([x-1, y-1])):
                pos.append([x-1, y-1])
                dfs(x-1, y-1, pos)

        self.virtual_pos = []  # store int coordinate
        dfs(0, 0, self.virtual_pos)

    def virtual_is_in(self, virtual_pos):
        """test if virtual_pos in rect"""
        real_pos = self.virtual_to_real(virtual_pos)
        x = real_pos[0]
        y = real_pos[1]
        if x < self.rect[0] or x > self.rect[0] + self.rect[2]:
            return False
        if y < self.rect[1] or y > self.rect[1] + self.rect[3]:
            return False
        return True

    def virtual_to_real(self, virtual_pos):
        real_x = virtual_pos[0] * math.sqrt(3) / 2 * self.factor + self.x_offset
        real_y = virtual_pos[1] / 2 * self.factor + self.y_offset
        return [real_x, real_y]

    def get_real_pos(self):
        real_pos = []
        for pos in self.virtual_pos:
            real_pos.append(self.virtual_to_real(pos))
        return real_pos

    def get_real_distance(self):
        return self.factor


class Agent:
    def __init__(self, virtual_pos):
        self.virtual_pos = virtual_pos

    def new_pos(self, virtual_pos_diff):
        return [self.virtual_pos[0] + virtual_pos_diff[0],
                self.virtual_pos[1] + virtual_pos_diff[1]]

    def move(self, virtual_pos_diff):
        self.virtual_pos = self.new_pos(virtual_pos_diff)

    def get_virtual_pos(self):
        return self.virtual_pos


class State:
    def __init__(self, rect, x_offset, y_offset, factor=1, n_agent=10):
        """
        Parameters
        ---------
        rect: [x, y, width, height]
            court size
        x_offset: float
            start point x
        y_offset: float
            start point y
        factor: int
            factor of edge of six-direction
        n_agent: int
            number of agent
        """
        self.position = Position(rect, x_offset, y_offset, factor)
        self.agents = None
        self.initial_agents()
        self.n_agent = n_agent

        self.virtual_actions = [[0, -2], [1, -1], [1, +1],
                                [0, 2], [-1, +1], [-1, -1]]

    def initial_agents(self):
        self.agents = []
        for random_virtual_pos in random.sample(self.position.virtual_pos, 10):
            self.agents.append(Agent(random_virtual_pos))

    def get_agent_number(self):
        return self.n_agent

    def get_legal_moves(self):
        return self.virtual_actions

    def get_successor_state(self, agent_id, move):
        assert move in self.virtual_actions

        agent = self.agents[agent_id]
        virtual_pos = agent.get_virtual_pos()
        new_virtual_pos = [sum(x) for x in zip(virtual_pos, move)]

        check = True
        if not self.virtual_pos_is_null(agent_id, new_virtual_pos):
            check = False
        if not self.position.virtual_is_in(new_virtual_pos):
            check = False

        new_state = copy.deepcopy(self)
        if check:
            new_state.agents[agent_id].move(move)
        return new_state

    def virtual_pos_is_null(self, agent_id, virtual_pos):
        for i, agent in enumerate(self.agents):
            if i == agent_id:
                continue
            if virtual_pos == agent.get_virtual_pos():
                return False
        return True

    def draw(self, surf, palette, x_offset, y_offset, factor=1):
        # position
        real_pos = self.position.get_real_pos()
        for pos in real_pos:
            x = int(pos[0] * factor + x_offset)
            y = int(pos[1] * factor + y_offset)
            pygame.draw.circle(surf, palette.black, [x, y], 2)

        # agent
        for i, agent in enumerate(self.agents):
            virtual_pos = agent.get_virtual_pos()
            real_pos = self.position.virtual_to_real(virtual_pos)
            x = int(real_pos[0] * factor + x_offset)
            y = int(real_pos[1] * factor + y_offset)
            r_agent = int(1. * self.position.get_real_distance() / 2 * factor)
            if i < self.n_agent / 2:
                pygame.draw.circle(surf, palette.red, [x, y], r_agent)
            else:
                pygame.draw.circle(surf, palette.blue, [x, y], r_agent)
