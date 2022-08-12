# -----------------------------------------------------------
# Code written by Wouter Apts
# Puzzle constraints can be changed at the bottom of the file
# -----------------------------------------------------------

from copy import deepcopy
import time
import pygame


class Tile:
    def __init__(self, name, pathways=None, possible_rot=0):
        self.name = name
        self.pathways = pathways

        self.paths_checked = []
        self.checked = False

        self.possible_rot = possible_rot

    def check(self, path_number):
        if self.pathways is None:
            self.checked = True
        else:
            self.paths_checked.append(path_number)
            if len(self.paths_checked) >= len(self.pathways):
                self.checked = True


def solve_puzzle(board, tileset, pos_constraints, neg_constraints):
    start = time.time()

    start_board = deepcopy(board)
    start_tileset = deepcopy(tileset)

    pos_constraints = sort_constraints(pos_constraints)

    neg_constraints = get_negative_constraints_in_pairs(neg_constraints)
    neg_constraints = sort_constraints(neg_constraints)

    no_isolation_constraint = get_no_isolation_constraint(pos_constraints)
    if place_valid_tile_on_board(start_board, (1, 1), start_tileset, pos_constraints, neg_constraints,
                                 no_isolation_constraint):
        end = time.time()
        print_board(start_board)
        print('Puzzle SOLVED in ')
        solve_time = "{:.3f}".format(end - start)
        print(str(solve_time) + 'seconds')
        draw_board(start_board)
    else:
        print('NO solution found')


def negative_constraints_met(connections_list, constraints):
    if len(constraints) == 0:
        return True
    for connection in connections_list:
        for constraint in constraints:
            overlap = list(set(connection).intersection(constraint))
            if len(overlap) >= 2:
                return False
    return True


def positive_constraints_met(connections_list, constraints):
    if len(constraints) == 0:
        return True
    for constraint in constraints:
        constraint_met = False
        for connection in connections_list:
            overlap = list(set(connection).intersection(constraint))
            if sorted(overlap) == sorted(constraint):
                constraint_met = True
                break
        if not constraint_met:
            return False
    return True


def sort_constraints(constraints):
    sorted_constraints = []
    for c in constraints:
        sorted_constraints.append(sorted(c))
    return sorted(sorted_constraints)


def place_valid_tile_on_board(board, index, tileset, pos_constraints, neg_constraints, no_isolation_constraint):
    available_tileset = deepcopy(tileset)
    checked_tileset = []
    cur_tile = None
    row = index[0]
    col = index[1]
    while len(available_tileset) > 0:
        print('.')
        if cur_tile is not None:
            checked_tileset.append(cur_tile)

        # grab the top tile from the available tileset.
        cur_tile = available_tileset.pop()

        # heuristic: check if a certain tile type has been tried already
        tile_type_checked = False
        for checked_tile in checked_tileset:
            if cur_tile.name == checked_tile.name:
                tile_type_checked = True

        if not tile_type_checked:
            tile_rot_left = cur_tile.possible_rot
            while tile_rot_left >= 0:
                print('..')
                if tile_placement_valid(board, (row, col), cur_tile, no_isolation_constraint):
                    append_tile_on_board(board, (row, col), cur_tile)
                    print('...')
                    # after placing tile, check if negative constraints are met:
                    if negative_constraints_met(get_connections_list(board), neg_constraints):
                        # get index of next cell in grid
                        next_row = row
                        next_col = col + 1
                        if next_col > 3:
                            next_row += 1
                            next_col = 1

                        # check if last tile has been placed, return True if positive constraints are met:
                        if next_row >= 4:
                            if positive_constraints_met(get_connections_list(board), pos_constraints):
                                # puzzle solved recursive end-point
                                return True

                        # if not the last cell, go to next cell in the grid and repeat the process
                        else:
                            # add all checked, but unusable tiles back to the next cell's tileset
                            next_tileset = checked_tileset + available_tileset
                            if place_valid_tile_on_board(board, (next_row, next_col), next_tileset, pos_constraints,
                                                         neg_constraints, no_isolation_constraint):
                                return True

                # if constraints are NOT met, remove the placed tile from the board and rotate it
                board[row][col] = None
                rotate_tile(cur_tile)
                tile_rot_left -= 1

    # return False when none of the available tiles fit (available tiles is empty)
    return False


def append_tile_on_board(board, index, tile):
    board[index[0]][index[1]] = tile


def tile_placement_valid(board, index, tile, no_isolation_constraint):
    # simplify current tile's path possibilities into a tuple
    cur_tile_paths = ()
    for p in tile.pathways:
        cur_tile_paths += p

    for n in range(0, 4):
        adj_tile_info = get_tile_info_in_direction(n, index[0], index[1])
        adj_tile = board[adj_tile_info[0][0]][adj_tile_info[0][1]]
        if adj_tile is None:
            continue
        elif adj_tile.pathways is not None:
            # simplify adjacent tile's path possibilities into a tuple
            adj_tile_paths = ()
            for p in adj_tile.pathways:
                adj_tile_paths += p

            if (n + 2) % 4 in adj_tile_paths:
                if n in cur_tile_paths:
                    continue
                # if no valid adjacent path is found return False
                else:
                    return False
            elif n in cur_tile_paths:
                return False
        elif (n not in cur_tile_paths) and (adj_tile.name in no_isolation_constraint):
            return False

    # if there are no invalid paths found return True
    return True


def rotate_tile(tile):
    new_pathways = []
    for path in tile.pathways:
        new_path = tuple((n + 1) % 4 for n in path)
        new_pathways.append(new_path)
    tile.pathways = new_pathways


def get_connections_list(board):
    board_copy = deepcopy(board)
    connections_list = []
    connections = []
    indices_left_to_check = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3)]

    # Start by checking the upper left tile with index (1,1), there is no previous tile.
    tilesToCheck = [((1, 1), None)]

    while len(tilesToCheck) > 0:
        cur_tile_info = tilesToCheck.pop()

        cur_tile_index = cur_tile_info[0]
        cur_tile = board_copy[cur_tile_index[0]][cur_tile_index[1]]

        # if there is no tile on that index, remove this index from indices_left_to_check
        if cur_tile is None:
            if cur_tile_index in indices_left_to_check:
                indices_left_to_check.remove(cur_tile_index)
        # if there is a tile, check if it has been completely checked yet
        elif cur_tile.checked is False:
            # add to connections if the tile is an item
            if cur_tile.pathways is None:
                connections.append(cur_tile.name)
                cur_tile.check(0)
            else:
                tilesToCheck.extend(get_next_tile_info(board_copy, cur_tile_info))
                if cur_tile.checked is True:
                    indices_left_to_check.remove(cur_tile_index)

        if len(tilesToCheck) == 0 and len(indices_left_to_check) > 0:
            tilesToCheck.append((indices_left_to_check[0], None))
            if len(connections) > 0:
                connections_list.append(sorted(connections))
                connections = []

    if len(connections) > 0:
        connections_list.append(sorted(connections))

    return sorted(connections_list)


def get_next_tile_info(board, cur_tile_info):
    next_tile_info = []
    cur_tile_index = cur_tile_info[0]
    prev_path_direction = cur_tile_info[1]

    row = cur_tile_index[0]
    col = cur_tile_index[1]
    cur_tile = board[row][col]

    if len(cur_tile.pathways) <= 1:
        for n in cur_tile.pathways[0]:
            if n is None:
                return None
            else:
                next_tile_info.append(get_tile_info_in_direction(n, row, col))
        cur_tile.check(0)
        return next_tile_info

    else:
        for p in range(0, 2):
            if p not in cur_tile.paths_checked:
                for n in cur_tile.pathways[p]:
                    if n is None:
                        return None
                    elif prev_path_direction is None:
                        next_tile_info.append(get_tile_info_in_direction(n, row, col))
                    elif (prev_path_direction + 2) % 4 in cur_tile.pathways[p]:
                        next_tile_info.append(get_tile_info_in_direction(n, row, col))
                if len(next_tile_info) != 0:
                    cur_tile.check(p)
                    return next_tile_info
    return next_tile_info


def get_tile_info_in_direction(n, row, col):
    match n:
        case 0:
            return (row - 1, col), n
        case 1:
            return (row, col + 1), n
        case 2:
            return (row + 1, col), n
        case 3:
            return (row, col - 1), n


def get_no_isolation_constraint(positive_constraints):
    return [item for sublist in positive_constraints for item in sublist]


def get_negative_constraints_in_pairs(negative_constraints):
    negative_constraints_in_pairs = []
    for constraint in negative_constraints:
        items = constraint[0]
        opposite_items = constraint[1]

        if isinstance(items, str) and isinstance(opposite_items, str):
            negative_constraints_in_pairs.append(constraint)

        elif isinstance(items, str):
            for opposite_item in opposite_items:
                paired_constraint = [items, opposite_item]
                negative_constraints_in_pairs.append(paired_constraint)

        elif isinstance(opposite_items, str):
            for item in items:
                paired_constraint = [item, opposite_items]
                negative_constraints_in_pairs.append(paired_constraint)

        else:
            for item in items:
                for opposite_item in opposite_items:
                    paired_constraint = [item, opposite_item]
                    negative_constraints_in_pairs.append(paired_constraint)

    return negative_constraints_in_pairs


def print_board(board):
    print('--------------')
    for r in range(1, 4):
        for c in range(1, 4):
            tile = board[r][c]
            if tile is not None:
                print(tile.pathways)
            else:
                print('Empty')
    print('--------------')


def draw_board(board):
    pygame.init()

    displaying = True
    while displaying:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                displaying = False
            if not displaying:
                pygame.quit()
        surface = pygame.display.set_mode((600, 600))
        surface_color = (12, 34, 68)
        surface.fill(surface_color)

        path_color = (200, 200, 45)
        for r in range(1, 4):
            for c in range(1, 4):
                tile = board[r][c]
                x_start = (c - 1) * 200 + 100
                y_start = (r - 1) * 200 + 100

                # don't draw empty tiles
                if tile is None:
                    continue

                # draw tiles with only one pathway
                elif len(tile.pathways) <= 1:
                    rect = pygame.Rect(0, 0, 35, 35)
                    rect.center = (x_start, y_start)
                    pygame.draw.rect(surface, path_color, rect)
                    x_end = 0
                    y_end = 0
                    for n in tile.pathways[0]:
                        match n:
                            case 0:
                                x_end = x_start
                                y_end = y_start - 100
                            case 1:
                                x_end = x_start + 100
                                y_end = y_start
                            case 2:
                                x_end = x_start
                                y_end = y_start + 100
                            case 3:
                                x_end = x_start - 100
                                y_end = y_start
                        pygame.draw.line(surface, path_color, (x_start, y_start), (x_end, y_end), width=35)

                # draw tiles with 2 pathways
                else:
                    for path in tile.pathways:
                        line = []
                        for n in path:
                            match n:
                                case 0:
                                    line.append((x_start - 100, y_start))
                                case 1:
                                    line.append((x_start, y_start + 100))
                                case 2:
                                    line.append((x_start + 100, y_start))
                                case 3:
                                    line.append((x_start, y_start - 100))
                        # check if tile is a bridge
                        if line[0][0] == line[1][0] or line[0][1] == line[1][1]:
                            pygame.draw.line(surface, surface_color, line[0], line[1], width=50)
                            pygame.draw.line(surface, path_color, line[0], line[1], width=35)
                        # or a two_bend
                        else:
                            pygame.draw.polygon(surface, path_color, (
                            (x_start - 100, y_start - 17), (x_start - 100, y_start + 17), (x_start - 83, y_start)))
                            pygame.draw.polygon(surface, path_color, (
                            (x_start + 100, y_start - 17), (x_start + 100, y_start + 17), (x_start + 83, y_start)))
                            pygame.draw.line(surface, path_color, line[0], line[1], width=35)

        # Drawing grid
        outline_color = (12, 28, 50)
        for x in [0, 200, 400]:
            pygame.draw.line(surface, outline_color, (x, 0), (x, 600), width=3)
        for y in [0, 200, 400]:
            pygame.draw.line(surface, outline_color, (0, y), (600, y), width=3)

        pygame.display.flip()


puzzle_tileset = [
    Tile('two-bends', [(0, 1), (2, 3)], 1),
    Tile('two-bends', [(0, 1), (2, 3)], 1),
    Tile('cross', [(0, 1, 2, 3)], 0),
    Tile('bend', [(0, 1)], 3),
    Tile('bend', [(0, 1)], 3),
    Tile('bend', [(0, 1)], 3),
    Tile('T-cross', [(0, 1, 2)], 3),
    Tile('T-cross', [(0, 1, 2)], 3),
    Tile('bridge', [(0, 2), (1, 3)], 0)
    ]

items = (Tile('ham'),
         Tile('cat'),
         Tile('cheese'),
         Tile('g_mouse'),
         Tile('r_house'),
         Tile('b_house'),
         Tile('b_dog'),
         Tile('tree'),
         Tile('thrash'),
         Tile('w_mouse'),
         Tile('r_dog'),
         Tile('bone')
         )

empty_board = [[None, items[0], items[1], items[2], None],
               [items[3], None, None, None, items[4]],
               [items[5], None, None, None, items[6]],
               [items[7], None, None, None, items[8]],
               [None, items[9], items[10], items[11], None]]

# -----------------------------------------------------------
# Puzzle constraints explained:
#
# Positive constraints are given by a yellow arrow, meaning there MUST be a pathway connecting the given items
# puzzle_pos_constraints = [['r_dog', 'b_dog'], ['g_mouse', 'w_mouse', 'cheese']]
# In this example there are 2 positive constraints, each given by a separate list
#
# Negative constraints are given by a red cross, meaning there CANNOT be a pathway connecting the given items.
# puzzle_neg_constraints = [['thrash', 'g_mouse'], ['b_dog', 'thrash'], [('g_mouse', 'w_mouse'), ('ham', 'r_house', 'cat', 'tree')]]
# In this example there are 3 negative constraints, each given by a separate list that contains exactly 2 elements (string or tuple)
# -----------------------------------------------------------

puzzle_pos_constraints = [['r_dog', 'r_house'], ['b_dog', 'tree', 'b_house', 'bone', 'ham', 'thrash']]
puzzle_neg_constraints = [[('r_dog', 'cheese'), 'thrash']]

solve_puzzle(empty_board, puzzle_tileset, puzzle_pos_constraints, puzzle_neg_constraints)
