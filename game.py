import sys
import pygame
import time
from math import pi


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
            print(rect, arc[1], arc[2])
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


class Basket(CourtLine):
    def __init__(self):
        super().__init__()
        self.lines.append(([6.6, 12.8], [8.4, 12.8]))
        self.lines.append(([7.5, 12.8], [7.5, 12.65]))
        self.circles.append(([7.5, 12.425], 0.225))


class Paint(CourtLine):
    def __init__(self):
        super().__init__()
        self.lines.append(([5.7, 8.2], [9.3, 8.2]))
        self.lines.append(([9.3, 8.2], [10.5, 14]))
        self.lines.append(([10.5, 14], [4.5, 14]))
        self.lines.append(([4.5, 14], [5.7, 8.2]))
        self.arcs.append(([5.7, 6.4, 3.6, 3.6], 0, pi))


class ThreePointLine(CourtLine):
    def __init__(self):
        super().__init__()
        self.lines.append(([1.25, 12.425], [1.25, 14]))
        self.lines.append(([13.75, 12.425], [13.75, 14]))
        self.arcs.append(([1.25, 6.175, 12.5, 12.5], 0, pi))


class MyColor:
    def __init__(self):
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)


class Game:
    def __init__(self):
        pygame.init()
        self.surf = pygame.display.set_mode((800, 600))

    def reset_surf(self, court_lines, palette):
        self.surf.fill(palette.white)
        for court_line in court_lines:
            court_line.draw(self.surf, palette, 50, 50, 30)
        pygame.display.update()


if __name__ == "__main__":
    palette = MyColor()
    game = Game()
    court_line = [Baseline(), Basket(), Paint(), ThreePointLine()]
    game.reset_surf(court_line, palette)
    time.sleep(5)
