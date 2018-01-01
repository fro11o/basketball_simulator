import sys
import pygame
import time
import math

from strategy import *
from state import *


class CourtLine:
    def __init__(self):
        self.lines = []  # element will be (start_pos, end_pos)
        self.arcs = []  # element will be (rect, start_angle, stop_angle)
        self.circles = []  # element will be (pos, radius)

    def draw(self, surf, palette, x_offset, y_offset, factor=1):
        for line in self.lines:
            start_pos = [int(_ * factor) for _ in line[0]]
            end_pos = [int(_ * factor) for _ in line[1]]
            start_pos[0] += int(x_offset)
            start_pos[1] += int(y_offset)
            end_pos[0] += int(x_offset)
            end_pos[1] += int(y_offset)
            pygame.draw.line(surf, palette.black, start_pos, end_pos, 2)
        for arc in self.arcs:
            rect = [int(_ * factor) for _ in arc[0]]
            rect[0] += int(x_offset)
            rect[1] += int(y_offset)
            pygame.draw.arc(surf, palette.black, rect, arc[1], arc[2], 2)
        for circle in self.circles:
            pos = [int(_ * factor) for _ in circle[0]]
            radius = int(circle[1] * factor)
            pos[0] += int(x_offset)
            pos[1] += int(y_offset)
            pygame.draw.circle(surf, palette.black, pos, radius, 2)


class Baseline(CourtLine):
    def __init__(self):
        super().__init__()
        self.lines.append(([0, 0], [15, 0]))
        self.lines.append(([15, 0], [15,14]))
        self.lines.append(([15, 14], [0, 14]))
        self.lines.append(([0, 14], [0, 0]))

    def get_rect(self):
        return [0, 0, 15, 14]


class Basket(CourtLine):
    def __init__(self):
        super().__init__()
        self.lines.append(([6.6, 12.8], [8.4, 12.8]))
        self.lines.append(([7.5, 12.8], [7.5, 12.65]))
        self.circles.append(([7.5, 12.425], 0.225))

    def get_basket(self):
        return [7.5, 12.425]


class Paint(CourtLine):
    def __init__(self):
        super().__init__()
        self.lines.append(([5.05, 8.2], [9.95, 8.2]))
        self.lines.append(([9.95, 8.2], [9.95, 14]))
        self.lines.append(([9.95, 14], [5.05, 14]))
        self.lines.append(([5.05, 14], [5.05, 8.2]))
        self.arcs.append(([5.7, 6.4, 3.6, 3.6], 0, math.pi))


class ThreePointLine(CourtLine):
    def __init__(self):
        super().__init__()
        self.lines.append(([0.75, 12.425], [0.75, 14]))
        self.lines.append(([14.25, 12.425], [14.25, 14]))
        self.arcs.append(([0.75, 5.675, 13.5, 13.5], 0, 1.03 * math.pi))


class MyColor:
    def __init__(self):
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.red = (255, 0, 0)
        self.green = (0, 255, 0)
        self.blue = (0, 0, 255)


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

        def virtual_to_real(virtual_pos):
            real_x = virtual_pos[0] * math.sqrt(3) / 2 * factor + x_offset
            real_y = virtual_pos[1] / 2 * factor + y_offset
            return [real_x, real_y]

        def is_in(rect, pos):
            """test if pos in rect"""
            x = pos[0]
            y = pos[1]
            if x < rect[0] or x > rect[0] + rect[2]:
                return False
            if y < rect[1] or y > rect[1] + rect[3]:
                return False
            return True

        def dfs(rect, x, y, pos):
            if ([x, y+2] not in pos and
                    is_in(rect, virtual_to_real([x, y+2]))):
                pos.append([x, y+2])
                dfs(rect, x, y+2, pos)
            if ([x, y-2] not in pos and
                    is_in(rect, virtual_to_real([x, y-2]))):
                pos.append([x, y-2])
                dfs(rect, x, y-2, pos)
            if ([x+1, y-1] not in pos and
                    is_in(rect, virtual_to_real([x+1, y-1]))):
                pos.append([x+1, y-1])
                dfs(rect, x+1, y-1, pos)
            if ([x+1, y+1] not in pos and
                    is_in(rect, virtual_to_real([x+1, y+1]))):
                pos.append([x+1, y+1])
                dfs(rect, x+1, y+1, pos)
            if ([x-1, y+1] not in pos and
                    is_in(rect, virtual_to_real([x-1, y+1]))):
                pos.append([x-1, y+1])
                dfs(rect, x-1, y+1, pos)
            if ([x-1, y-1] not in pos and
                    is_in(rect, virtual_to_real([x-1, y-1]))):
                pos.append([x-1, y-1])
                dfs(rect, x-1, y-1, pos)

        self.virtual_pos = []  # store int coordinate
        dfs(rect, 0, 0, self.virtual_pos)

        self.real_pos = []
        for pos in self.virtual_pos:
            self.real_pos.append(virtual_to_real(pos))

    def get_real_pos(self):
        return self.real_pos

    def draw(self, surf, palette, x_offset, y_offset, factor=1):
        for pos in self.real_pos:
            x = int(pos[0] * factor + x_offset)
            y = int(pos[1] * factor + y_offset)
            pygame.draw.circle(surf, palette.black, [x, y], 2)

class Game:
    def __init__(self):
        pygame.init()
        self.surf = pygame.display.set_mode((800, 600))


    def reset_surf(self, palette, court_lines, state):
        self.surf.fill(palette.white)
        for court_line in court_lines:
            court_line.draw(self.surf, palette, 50, 50, 30)
        state.draw(self.surf, palette, 50, 50, 30)
        pygame.display.update()


if __name__ == "__main__":
    palette = MyColor()
    game = Game()
    court_line = [Baseline(), Basket(), Paint(), ThreePointLine()]
    state = State(court_line[0].get_rect(),
                  court_line[1].get_basket()[0],
                  court_line[1].get_basket()[1],
                  0.9)

    #defense_strategy = Brownian()
    defense_strategy = Oneonone()
    #offense_strategy = Brownian()
    offense_strategy = Minimax()
    while True:
        moves = []
        # offense strategy
        for agent_id in range(state.n_agent):
            if agent_id >= state.get_agent_number() / 2:
                continue
            move = offense_strategy.next_move(agent_id, state)
            moves.append(move)
        # defense strategy
        for agent_id in range(state.n_agent):
            if agent_id < state.get_agent_number() / 2:
                continue
            move = defense_strategy.next_move(agent_id, state)
            moves.append(move)
        game.reset_surf(palette, court_line, state)
        time.sleep(1)
        # get new state after moves sequence
        for i in range(state.n_agent):
            state = state.get_successor_state(i, moves[i])
