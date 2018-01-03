import sys
import pygame
import time
import math
from pygame.locals import *

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
        self.start_button = [500, 500, 100, 50]
        self.court_factor = 30
        self.court_x_offset = 50
        self.court_y_offset = 50

    def reset_surf(self, palette, court_lines, state, link=False):
        self.surf.fill(palette.white)
        for court_line in court_lines:
            court_line.draw(self.surf, palette, self.court_x_offset, self.court_y_offset, self.court_factor)
        state.draw(self.surf, palette, self.court_x_offset, self.court_y_offset, self.court_factor, link)
        pygame.draw.rect(self.surf, (200, 200, 200), self.start_button)
        pygame.display.update()

    def is_start_button(self, pos):
        check = True
        if pos[0] < self.start_button[0] or pos[0] > self.start_button[0] + self.start_button[2]:
            check = False
        if pos[1] < self.start_button[1] or pos[1] > self.start_button[1] + self.start_button[3]:
            check = False
        return check


def get_vpos_link(game, state):
    vpos_stand_place_link = []
    vpos_pair = []
    while True:
        mouse_clicked = False
        check_ready = False
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONUP:
                mouse_x, mouse_y = event.pos
                if game.is_start_button([mouse_x, mouse_y]):
                    check_ready = True
                    break
                rx = mouse_x
                ry = mouse_y
                rx -= game.court_x_offset
                ry -= game.court_y_offset
                rx = rx / game.court_factor
                ry = ry / game.court_factor
                vpos = state.real_to_close_virtual([rx, ry])
                if vpos is None:
                    continue
                if event.button == 1:  # left click
                    vpos_pair.append(vpos)
                    if len(vpos_pair) == 2:
                        vpos_stand_place_link.append(vpos_pair[:])
                        vpos_pair = []
        state.set_agents([], [], vpos_stand_place_link)
        game.reset_surf(palette, court_line, state, link=True)
        time.sleep(0.1)
        if check_ready:
            break


def get_vpos_start(game, state):
    vpos_start_offense = []
    vpos_start_defense = []
    while True:
        mouse_clicked = False
        check_ready = False
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONUP:
                mouse_x, mouse_y = event.pos
                if game.is_start_button([mouse_x, mouse_y]) and\
                len(vpos_start_offense) == int(state.n_agent / 2) and\
                len(vpos_start_defense) == int(state.n_agent / 2):
                    check_ready = True
                    break
                rx = mouse_x
                ry = mouse_y
                rx -= game.court_x_offset
                ry -= game.court_y_offset
                rx = rx / game.court_factor
                ry = ry / game.court_factor
                vpos = state.real_to_close_virtual([rx, ry])
                if vpos is None:
                    continue
                if event.button == 1:  # left click
                    if vpos in vpos_start_offense:
                        tmp = []
                        for x in vpos_start_offense:
                            if x != vpos:
                                tmp.append(x)
                        vpos_start_offense = tmp
                    elif len(vpos_start_offense) < int(state.n_agent / 2):
                        vpos_start_offense.append(vpos)
                elif event.button == 3:  # right click
                    if vpos in vpos_start_defense:
                        tmp = []
                        for x in vpos_start_defense:
                            if x != vpos:
                                tmp.append(x)
                        vpos_start_defense = tmp
                    elif len(vpos_start_defense) < int(state.n_agent / 2):
                        vpos_start_defense.append(vpos)
        state.set_agents(vpos_start_offense, vpos_start_defense)
        game.reset_surf(palette, court_line, state, link=True)
        time.sleep(0.1)
        if check_ready:
            break


if __name__ == "__main__":
    palette = MyColor()
    game = Game()
    court_line = [Baseline(), Basket(), Paint(), ThreePointLine()]
    state = State(court_line[0].get_rect(),
                  court_line[1].get_basket()[0],
                  court_line[1].get_basket()[1],
                  factor=0.9,
                  n_agent=6)

    game.reset_surf(palette, court_line, state)

    get_vpos_link(game, state)
    get_vpos_start(game, state)
    """
    vpos_start_offense = []
    vpos_start_defense = []
    vpos_stand_place_link = []
    while True:
        mouse_clicked = False
        check_ready = False
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONUP:
                mouse_x, mouse_y = event.pos
                if game.is_start_button([mouse_x, mouse_y]) and\
                len(vpos_start_offense) == int(state.n_agent / 2) and\
                len(vpos_start_defense) == int(state.n_agent / 2):
                    check_ready = True
                    break
                rx = mouse_x
                ry = mouse_y
                rx -= game.court_x_offset
                ry -= game.court_y_offset
                rx = rx / game.court_factor
                ry = ry / game.court_factor
                vpos = state.real_to_close_virtual([rx, ry])
                if vpos is None:
                    continue
                if event.button == 1:  # left click
                    if vpos in vpos_start_offense:
                        tmp = []
                        for x in vpos_start_offense:
                            if x != vpos:
                                tmp.append(x)
                        vpos_start_offense = tmp
                    elif len(vpos_start_offense) < int(state.n_agent / 2):
                        vpos_start_offense.append(vpos)
                elif event.button == 3:  # right click
                    if vpos in vpos_start_defense:
                        tmp = []
                        for x in vpos_start_defense:
                            if x != vpos:
                                tmp.append(x)
                        vpos_start_defense = tmp
                    elif len(vpos_start_defense) < int(state.n_agent / 2):
                        vpos_start_defense.append(vpos)
        vpos_start_offense, vpos_start_defense = get_vpos_start(game, state)
        state.set_agents(vpos_start_offense, vpos_start_defense, [])
        game.reset_surf(palette, court_line, state)
        time.sleep(0.1)
        if check_ready:
            break
    """

    p_screen = 0.2  # prob that defense_agent could catch up
    p_unscreen = 0.8  # prob that defense_agent could catch up under screen

    #defense_strategy = Brownian()
    defense_strategy = MotionDefense()
    #offense_strategy = Brownian()
    offense_strategy = MotionOffense(p_screen, p_unscreen)

    """
    while True:
        moves = []
        # offense strategy

        for agent_id in range(state.n_agent):
            if agent_id >= int(state.get_agent_number() / 2):
                continue
            move = offense_strategy.next_move(agent_id, state)
            moves.append(move)
        # defense strategy
        for agent_id in range(state.n_agent):
            if agent_id < int(state.get_agent_number() / 2):
                continue
            move = defense_strategy.next_move(agent_id, state)
            moves.append(move)
        game.reset_surf(palette, court_line, state)
        time.sleep(0.5)
        # get new state after moves sequence
        for i in range(state.n_agent):
            state = state.get_successor_state(i, moves[i])
    """
    time_step = 1

    while True:
        move, log_p = offense_strategy.next_move(state, time_step)
        time_step -= 1
        if time_step == 0:
            break
    time.sleep(10000)
