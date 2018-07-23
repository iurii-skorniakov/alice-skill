# coding: utf-8

from __future__ import unicode_literals

import random
import re
import logging

from transliterate import translit

from seabattle.strategy import Strategy, DamagedShipStrategy, Point, RandomStrategy
EMPTY = 0
SHIP = 1
BLOCKED = 2
HIT = 3
MISS = 4

log = logging.getLogger(__name__)


class BaseGame(object):
    position_patterns = [re.compile('^([a-zа-я]+)(\d+)$', re.UNICODE),  # a1
                         re.compile('^([a-zа-я]+)\s+(\w+)$', re.UNICODE),  # a 1; a один
                         re.compile('^(\w+)\s+(\w+)$', re.UNICODE),  # a 1; a один; 7 10
                         ]

    str_letters = ['а', 'б', 'в', 'г', 'д', 'е', 'ж', 'з', 'и', 'к']
    str_numbers = ['один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять', 'десять']

    letters_mapping = {
        'the': 'з',
        'за': 'з',
        'уже': 'ж',
        'трень': '3',
    }

    default_ships = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

    def __init__(self):
        self.size = 0
        self.ships = None
        self.field = []
        self.enemy_field = []

        self.ships_count = 0
        self.enemy_ships_count = 0

        self.last_shot_position = None
        self.last_enemy_shot_position = None
        self.numbers = None

    def start_new_game(self, size=10, field=None, ships=None, numbers=None):
        assert(size <= 10)
        assert(len(field) == size ** 2 if field is not None else True)

        self.size = size
        self.numbers = numbers if numbers is not None else False

        if ships is None:
            self.ships = self.default_ships
        else:
            self.ships = ships

        if field is None:
            self.generate_field()
        else:
            self.field = field

        self.enemy_field = [EMPTY] * self.size ** 2

        self.ships_count = self.enemy_ships_count = len(self.ships)

        self.last_shot_position = None
        self.last_enemy_shot_position = None

    def generate_field(self):
        raise NotImplementedError()

    def print_field(self, field=None):
        if not self.size:
            log.info('Empty field')
            return

        if field is None:
            field = self.field

        mapping = ['.', '1', '.', 'X', 'x']

        lines = ['']
        lines.append('-' * (self.size + 2))
        for y in range(self.size):
            lines.append('|%s|' % ''.join(str(mapping[x]) for x in field[y * self.size: (y + 1) * self.size]))
        lines.append('-' * (self.size + 2))
        log.info('\n'.join(lines))

    def print_enemy_field(self):
        self.print_field(self.enemy_field)

    def handle_enemy_shot(self, position):
        index = self.calc_index(position)

        if self.field[index] == SHIP:
            self.field[index] = HIT

            if self.is_dead_ship(index):
                self.ships_count -= 1
                return 'kill'
            else:
                return 'hit'
        elif self.field[index] == HIT:
            return 'kill' if self.is_dead_ship(index) else 'hit'
        else:
            return 'miss'

    def is_dead_ship(self, last_index):
        x, y = self.calc_position(last_index)
        x -= 1
        y -= 1

        def _line_is_dead(line, index):
            def _tail_is_dead(tail):
                for i in tail:
                    if i == HIT:
                        continue
                    elif i == SHIP:
                        return False
                    else:
                        return True
                return True

            return _tail_is_dead(line[index:]) and _tail_is_dead(line[index::-1])

        return (
            _line_is_dead(self.field[x::self.size], y) and
            _line_is_dead(self.field[y * self.size:(y + 1) * self.size], x)
        )

    def is_end_game(self):
        return self.is_victory() or self.is_defeat()

    def is_victory(self):
        return self.enemy_ships_count < 1

    def is_defeat(self):
        return self.ships_count < 1

    def do_shot(self):
        raise NotImplementedError()

    def repeat(self):
        return self.convert_from_position(self.last_shot_position, numbers=True)

    def reset_last_shot(self):
        self.last_shot_position = None

    def handle_enemy_reply(self, message):
        if self.last_shot_position is None:
            return

        index = self.calc_index(self.last_shot_position)

        if message in ['hit', 'kill']:
            self.enemy_field[index] = SHIP

            if message == 'kill':
                self.enemy_ships_count -= 1

        elif message == 'miss':
            self.enemy_field[index] = MISS

    def calc_index(self, position):
        x, y = position

        if x > self.size or y > self.size:
            raise ValueError('Wrong position: %s %s' % (x, y))

        return (y - 1) * self.size + x - 1

    def calc_position(self, index):
        y = index / self.size + 1
        x = index % self.size + 1

        return x, y

    def convert_to_position(self, position):
        position = position.lower()
        for pattern in self.position_patterns:
            match = pattern.match(position)

            if match is not None:
                break
        else:
            raise ValueError('Can\'t parse entire position: %s' % position)

        bits = match.groups()

        def _try_letter(bit):
            # проверяем особые случаи неправильного распознования STT
            bit = self.letters_mapping.get(bit, bit)

            # преобразуем в кириллицу
            bit = translit(bit, 'ru')

            try:
                return self.str_letters.index(bit) + 1
            except ValueError:
                raise

        def _try_number(bit):
            # проверяем особые случаи неправильного распознования STT
            bit = self.letters_mapping.get(bit, bit)

            if bit.isdigit():
                return int(bit)
            else:
                try:
                    return self.str_numbers.index(bit) + 1
                except ValueError:
                    raise

        x = bits[0].strip()
        try:
            x = _try_number(x)
        except ValueError:
            raise ValueError('Can\'t parse X point: %s' % x)

        y = bits[1].strip()
        try:
            y = _try_number(y)
        except ValueError:
            raise ValueError('Can\'t parse Y point: %s' % y)

        return x, y

    def convert_from_position(self, position, numbers=None):
        numbers = numbers if numbers is not None else self.numbers

        if numbers:
            x = position[0]
        else:
            x = self.str_letters[position[0] - 1]

        y = position[1]

        return '%s, %s' % (x, y)


class Game(BaseGame):
    """Реализация игры с ипользованием обычного random"""

    def __init__(self):
        self.strategy = Strategy(region_size=4)
        self.damaged_ship_strategy = None

        self.four_decker_count = 1
        self.three_decker_count = 2
        self.two_decker_count = 3
        self.one_decker_count = 4

        self.four_decker_strategy = Strategy(region_size=4)
        self.three_decker_strategy = Strategy(region_size=3)
        self.two_decker_strategy = Strategy(region_size=2)
        self.one_decker_strategy = RandomStrategy(game=self)
        super(Game, self).__init__()



    def generate_field(self):
        """Метод генерации поля"""
        self.field = [0] * self.size ** 2

        for length in self.ships:
            self.place_ship(length)

        for i in range(len(self.field)):
            if self.field[i] == BLOCKED:
                self.field[i] = EMPTY

    def place_ship(self, length):
        def _try_to_place():
            x = random.randint(1, self.size)
            y = random.randint(1, self.size)
            direction = random.choice([1, self.size])

            index = self.calc_index((x, y))
            values = self.field[index:None if direction == self.size else index + self.size - index % self.size:direction][:length]

            if len(values) < length or any(values):
                return False

            for i in range(length):
                current_index = index + direction * i

                for j in [0, 1, -1]:
                    if (j != 0
                            and current_index % self.size in (0, self.size - 1)
                            and (current_index + j) % self.size in (0, self.size - 1)):
                        continue

                    for k in [0, self.size, -self.size]:
                        neighbour_index = current_index + k + j

                        if (neighbour_index < 0
                                or neighbour_index >= len(self.field)
                                or self.field[neighbour_index] == SHIP):
                            continue

                        self.field[neighbour_index] = BLOCKED

                self.field[current_index] = SHIP

            return True

        while not _try_to_place():
            pass

    def do_shot(self):
        while True:
            point_to_shoot = self.strategy.get_shoot_point()
            if self.enemy_field[self.calc_index(point_to_shoot)] == EMPTY:
                self.last_shot_position = self.strategy.get_shoot_point()
                return self.convert_from_position(self.last_shot_position)

    def handle_enemy_reply(self, message):
        if self.last_shot_position is None:
            return

        index = self.calc_index(self.last_shot_position)

        if message in ['hit', 'kill']:
            self.enemy_field[index] = SHIP
            if self.damaged_ship_strategy is None:
                self.damaged_ship_strategy = DamagedShipStrategy()
                self.damaged_ship_strategy.add_ship_point(self.last_shot_position)

            if message == 'kill':
                self.enemy_ships_count -= 1

                self._mark_nearby_ship_points_as_miss()
                self.reduce_enemy_ships_count(len(self.damaged_ship_strategy.ship))
                self.damaged_ship_strategy = None
                self._set_strategy()

        elif message == 'miss':
            self.enemy_field[index] = MISS

    def _mark_nearby_ship_points_as_miss(self):
        for point in self.damaged_ship_strategy.get_nearby_ship_points():
            try:
                index = self.calc_index(point)
            except ValueError:
                continue

            if self.enemy_field[index] == EMPTY:
                self.enemy_field[index] = MISS

    def _set_strategy(self):
        if self.four_decker_count:
            self.strategy = self.four_decker_strategy
        elif self.three_decker_count:
            self.strategy = self.three_decker_strategy
        elif self.two_decker_count:
            self.strategy = self.two_decker_strategy
        else:
            self.strategy = self.one_decker_strategy

    def reduce_enemy_ships_count(self, deckers):
        if deckers == 4:
            self.four_decker_count -= 1
        if deckers == 3:
            self.three_decker_count -= 1
        if deckers == 2:
            self.two_decker_count -= 1
        if deckers == 1:
            self.one_decker_count -= 1
