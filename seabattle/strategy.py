# coding: utf-8
import random
from collections import namedtuple

Region = namedtuple('Point', ['start_x', 'start_y', 'end_x', 'end_y'])


class AbstractStrategy(object):
    def get_shoot_point(self):
        raise NotImplementedError


class Strategy(AbstractStrategy):
    def __init__(self, size=10, region_size=4):
        self.size = size
        self.region_size = region_size
        self.regions = self.get_regions()
        self.combination = self.get_combination()
        self.shooting_field = self.get_shooting_field()

    def get_shoot_point(self):
        return self.shooting_field.pop()

    def get_combination(self):
        combination = []
        lst = [x for x in range(self.region_size)]
        random.shuffle(lst)
        for i in lst:
            row = [0 if x != i else 1 for x in range(self.region_size)]
            combination.append(row)
        return combination

    def get_shooting_field(self):
        shooting_field = []
        for region in self.regions:
            for x in range(region.start_x, region.end_x + 1):
                local_x = x - region.start_x
                for y in range(region.start_y, region.end_y + 1):
                    local_y = y - region.start_y
                    if self.combination[local_y][local_x] == 1:
                        shooting_field.append(Point(x, y))
        return shooting_field

    def get_regions(self):
        def get_points(start_c):
            points = [(1, start_c - 1)] if start_c > 1 else []
            return points + [(c, get_end_coord(c)) for c in range(start_c, self.size + 1, self.region_size)]

        def get_end_coord(coord):
            end_coord = coord + self.region_size-1
            return end_coord if end_coord < self.size else self.size
        delta = self.size % self.region_size
        x_points = get_points(random.randint(1, delta+1))
        y_points = get_points(random.randint(1, delta+1))

        regions = []
        for start_x, end_x in x_points:
            for start_y, end_y in y_points:
                regions.append(Region(start_x, start_y, end_x, end_y))
        return regions


Point = namedtuple('Point', ['x', 'y'])


class DamagedShipStrategy(AbstractStrategy):
    def get_shoot_point(self):
        return self.shoot_field.pop()

    def __init__(self):
        self.ship = []
        self.shoot_field = []
        self.dimension = None
        self.index = None

    def add_ship_point(self, point):
        self.ship.append(point)
        nearby_points = self.get_nearby_line_points(point)
        self.shoot_field += nearby_points
        if len(self.ship) == 1:
            return
        if self.dimension is None:
            self.get_ship_dimension()
        self.shoot_field = [point for point in self.shoot_field if getattr(point, self.dimension) == self.index]

    def get_ship_dimension(self):
        first = self.ship[0]
        second = self.ship[1]
        if first.x == second.x:
            self.dimension = 'x'
            self.index = first.x
        else:
            self.dimension = 'y'
            self.index = first.y

    def get_nearby_line_points(self, point):
        return [
            Point(point.x+1, point.y),
            Point(point.x-1, point.y),
            Point(point.x, point.y+1),
            Point(point.x, point.y-1),
        ]

    def get_nearby_diagonal_points(self, point):
        return [
            Point(point.x + 1, point.y + 1),
            Point(point.x - 1, point.y - 1),
            Point(point.x - 1, point.y + 1),
            Point(point.x + 1, point.y - 1),
        ]

    def get_nearby_ship_points(self):
        ship_points = set(self.ship)
        points = []
        for ship_point in self.ship:
            for point in self.get_nearby_line_points(ship_point):
                if point not in ship_points:
                    points.append(point)
            for point in self.get_nearby_diagonal_points(ship_point):
                if point not in ship_points:
                    points.append(point)
        return points


class RandomStrategy(AbstractStrategy):

    def __init__(self, game):
        self.game = game

    def get_shoot_point(self):
        index = random.choice([i for i, v in enumerate(self.game.enemy_field) if v == 0])
        return self.game.calc_position(index)


if __name__ == '__main__':
    a = Strategy(region_size=4)
    assert len(a.regions) >= 9
    assert len(a.shooting_field) >= 26
