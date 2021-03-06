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

    def get_shortest_path(self, a, b):
        legal_moves = [[0, -2], [1, -1], [1, 1],
                       [0, 2], [-1, 1], [-1, -1]]
        check_list = {}
        queue = [a]
        check_list[str(a)] = None

        while len(queue) > 0:
            x = queue[0]
            queue = queue[1:]
            for legal_move in legal_moves:
                new_x = [x[0] + legal_move[0], x[1] + legal_move[1]]
                if new_x in self.virtual_pos and str(new_x) not in check_list:
                    check_list[str(new_x)] = x
                    queue.append(new_x)

        path = [b]
        cur = b
        while a not in path:
            path.append(check_list[str(cur)])
            cur = check_list[str(cur)]
        return path[::-1]

    def virtual_distance(self, a, b):
        return len(self.get_shortest_path(a, b))

    def real_distance(self, a, b):
        real_a = self.virtual_to_real(a)
        real_b = self.virtual_to_real(b)
        diff_x = real_a[0] - real_b[0]
        diff_y = real_a[1] - real_b[1]
        return pow(pow(diff_x, 2) + pow(diff_y, 2), 0.5)

class Agent:
    def __init__(self, virtual_pos):
        self.virtual_pos = virtual_pos

    def set_vpos(self, vpos):
        self.virtual_pos = vpos

    def new_virtual_pos(self, virtual_pos_diff):
        return [self.virtual_pos[0] + virtual_pos_diff[0],
                self.virtual_pos[1] + virtual_pos_diff[1]]

    def move(self, virtual_pos_diff):
        self.virtual_pos = self.new_virtual_pos(virtual_pos_diff)

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
        self.n_agent = n_agent
        self.agents = []
        self.ball_agent_id = None
        self.stand_place = []
        self.stand_place_link = {}
        self.screen_one = []
        self.run_one = []
        self.log_p = 0

        self.virtual_actions = [[0, -2], [1, -1], [1, +1],
                                [0, 2], [-1, +1], [-1, -1], [0, 0]]

    def set_agents(self, vpos_offense_agents, vpos_defense_agents, vpos_stand_place_link=None):
        self.agents = [None] * (len(vpos_offense_agents) + len(vpos_defense_agents))
        for i, vpos in enumerate(vpos_offense_agents):
            self.agents[i] = Agent(vpos)
        for i, vpos in enumerate(vpos_defense_agents):
            self.agents[i+len(vpos_offense_agents)] = Agent(vpos)
        if vpos_stand_place_link is not None:
            self.stand_place = []
            self.stand_place_link = {}
            for pair in vpos_stand_place_link:
                if pair[0] not in self.stand_place:
                    self.stand_place.append(pair[0])
                if pair[1] not in self.stand_place:
                    self.stand_place.append(pair[1])
                if str(pair[0]) not in self.stand_place_link:
                    self.stand_place_link[str(pair[0])] = []
                if pair[1] not in self.stand_place_link[str(pair[0])]:
                    self.stand_place_link[str(pair[0])].append(pair[1])
                if str(pair[1]) not in self.stand_place_link:
                    self.stand_place_link[str(pair[1])] = []
                if pair[0] not in self.stand_place_link[str(pair[1])]:
                    self.stand_place_link[str(pair[1])].append(pair[0])
        self.ball_agent_id = 0

    def my_deep_copy(self):
        self.agents = copy.deepcopy(self.agents)
        self.screen_one = copy.deepcopy(self.screen_one)
        self.run_one = copy.deepcopy(self.run_one)

    def get_agent_number(self):
        return self.n_agent

    def get_legal_moves(self):
        """
        def dfs(move, unit_moves, steps):
            if steps == 0:
                return [move]
            ret = []
            for unit_move in unit_moves:
                new_move = [sum(x) for x in zip(move, unit_move)]
                for x in dfs(new_move, unit_moves, steps - 1):
                    if x not in ret:
                        ret.append(x)
                #ret.extend(dfs(new_move, unit_moves, steps - 1))
            return ret
        return dfs([0, 0], self.virtual_actions, 3)
        """
        return self.virtual_actions

    def move_agent_to(self, agent_id, vpos):
        self.agents[agent_id].set_vpos(vpos)

    def get_successor_state(self, agent_id, move):
        agent = self.agents[agent_id]
        virtual_pos = agent.get_virtual_pos()
        new_virtual_pos = [sum(x) for x in zip(virtual_pos, move)]

        check = True
        if not self.virtual_pos_is_null(agent_id, new_virtual_pos):
            check = False
        if not self.position.virtual_is_in(new_virtual_pos):
            check = False

        #new_state = copy.deepcopy(self)
        new_state = copy.copy(self)
        new_state.my_deep_copy()
        #new_state.agents = copy.deepcopy(self.agents)
        if check:
            new_state.agents[agent_id].move(move)
        return new_state

    def get_agent_virtual_pos(self, agent_id):
        try:
            return self.agents[agent_id].get_virtual_pos()
        except:
            return None

    def get_basket_virtual_pos(self):
        return [0, 0]

    def get_shortest_path(self, a, b):
        return self.position.get_shortest_path(a, b)

    def virtual_pos_is_null(self, agent_id, virtual_pos):
        for i, agent in enumerate(self.agents):
            if i == agent_id:
                continue
            if virtual_pos == agent.get_virtual_pos():
                return False
        return True

    def basket_distance(self, agent_id):
        assert agent_id < self.n_agent / 2

        vpos_agent = self.get_agent_virtual_pos(agent_id)
        vpos_basket = self.get_basket_virtual_pos()

        return self.position.real_distance(vpos_agent, vpos_basket)

    def defense_distance(self, agent_id):
        def cross_product(a, b):
            return a[0] * b[0] + a[1] * b[1]

        assert agent_id < self.n_agent / 2
        vpos_defense_agents = []
        for i in range(self.n_agent):
            if i >= int(self.n_agent / 2):
                vpos_defense_agents.append(self.get_agent_virtual_pos(i))
        vpos_basket = self.get_basket_virtual_pos()
        min_distance = None
        min_agent_id = None
        for j in range(len(vpos_defense_agents)):
            virtual_off = self.get_agent_virtual_pos(agent_id)
            virtual_def = vpos_defense_agents[j]
            real_off = self.position.virtual_to_real(virtual_off)
            real_def = self.position.virtual_to_real(virtual_def)
            real_basket = self.position.virtual_to_real(vpos_basket)
            vector_off = [a - b for a, b in zip(real_basket, real_off)]
            vector_def = [a - b for a, b in zip(real_def, real_off)]
            if cross_product(vector_off, vector_def) > 0:
                if min_distance is None or self.position.real_distance(virtual_off, virtual_def) < min_distance:
                    min_distance = self.position.real_distance(virtual_off, virtual_def)
                    min_agent_id = j + int(self.n_agent / 2)
        if min_distance is None:
            return -1, None
        return min_distance, min_agent_id

    def is_open(self, agent_id):
        real_three_point = 6.75
        if self.basket_distance(agent_id) < real_three_point+1 and self.defense_distance(agent_id)[0] < 0:
            return True
        return False

    def real_to_close_virtual(self, rpos_mouse):
        def real_distance(a, b):
            return pow(pow(a[0] - b[0], 2) + pow(a[1] - b[1], 2), 0.5)
        for vpos in self.position.virtual_pos:
            rpos = self.position.virtual_to_real(vpos)
            if real_distance(rpos_mouse, rpos) < 0.5:
                return vpos
        return None

    def draw(self, surf, palette, x_offset, y_offset, factor=1):
        # position
        real_pos = self.position.get_real_pos()
        for pos in real_pos:
            x = int(pos[0] * factor + x_offset)
            y = int(pos[1] * factor + y_offset)
            pygame.draw.circle(surf, (220, 220, 220), [x, y], 2)

        # link
        for v1 in self.stand_place:
            for v2 in self.stand_place_link[str(v1)]:
                real_pos = self.position.virtual_to_real(v1)
                x = int(real_pos[0] * factor + x_offset)
                y = int(real_pos[1] * factor + y_offset)
                surf_v1 = [x, y]
                real_pos = self.position.virtual_to_real(v2)
                x = int(real_pos[0] * factor + x_offset)
                y = int(real_pos[1] * factor + y_offset)
                surf_v2 = [x, y]
                pygame.draw.line(surf, palette.green, surf_v1, surf_v2, 2)

        # agent
        for i, agent in enumerate(self.agents):
            if agent is None:
                continue
            virtual_pos = agent.get_virtual_pos()
            real_pos = self.position.virtual_to_real(virtual_pos)
            x = int(real_pos[0] * factor + x_offset)
            y = int(real_pos[1] * factor + y_offset)
            r_agent = int(1. * self.position.get_real_distance() / 2 * factor)
            if i < self.n_agent / 2:
                if i == self.ball_agent_id:  # draw ball_agent_id
                    pygame.draw.circle(surf, palette.red, [x, y], r_agent)
                    pygame.draw.circle(surf, palette.white, [x, y], r_agent - 2)
                    font = pygame.font.Font(None, 24)
                    agent_id_text = font.render(str(i), 1, (0, 0, 0))
                    surf.blit(agent_id_text, [x - int(r_agent / 2), y - int(r_agent / 2)])
                else:
                    pygame.draw.circle(surf, palette.red, [x, y], r_agent)
                    font = pygame.font.Font(None, 24)
                    agent_id_text = font.render(str(i), 1, (255, 255, 255))
                    surf.blit(agent_id_text, [x - int(r_agent / 2), y - int(r_agent / 2)])
            else:
                pygame.draw.circle(surf, palette.blue, [x, y], r_agent)
                font = pygame.font.Font(None, 24)
                agent_id_text = font.render(str(i), 1, (255, 255, 255))
                surf.blit(agent_id_text, [x - int(r_agent / 2), y - int(r_agent / 2)])


