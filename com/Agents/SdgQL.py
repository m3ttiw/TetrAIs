from com.Core.BaseGame import BaseGame
from abc import ABC
import copy
from com.Core.Model import PIECES, BOARDWIDTH, BOARDHEIGHT, is_valid_position, add_to_board, \
    remove_complete_lines
import sys
import random
import math

weights = [-1, -1, -1, -30]  # Initial weight vector


class SDG_QL(BaseGame, ABC):

    def __init__(self, r_p):
        super().__init__(r_p)
        self.alpha = 0.01
        self.gamma = 0.9
        self.explore_change = 0
        #self.weights = globalWeights  #[-1, -1, -1, -30]

    def get_move(self):
        return self.sdg(self.board, self.falling_piece)

    def get_parameters_x(self, board):
        # This function will calculate different parameters of the current board

        # Initialize some stuff
        heights = [0] * BOARDWIDTH
        diffs = [0] * (BOARDWIDTH - 1)
        holes = 0
        diff_sum = 0

        # Calculate the maximum height of each column
        for i in range(0, BOARDWIDTH):  # Select a column
            for j in range(0, BOARDHEIGHT):  # Search down starting from the top of the board
                if int(board[i][j]) > 0:  # Is the cell occupied?
                    heights[i] = BOARDHEIGHT - j  # Store the height value
                    break

        # Calculate the difference in heights
        for i in range(0, len(diffs)):
            diffs[i] = heights[i + 1] - heights[i]

        # Calculate the maximum height
        max_height = max(heights)

        # Count the number of holes
        for i in range(0, BOARDWIDTH):
            occupied = 0  # Set the 'Occupied' flag to 0 for each new column
            for j in range(0, BOARDHEIGHT):  # Scan from top to bottom
                if int(board[i][j]) > 0:
                    occupied = 1  # If a block is found, set the 'Occupied' flag to 1
                if int(board[i][j]) == 0 and occupied == 1:
                    holes += 1  # If a hole is found, add one to the count

        height_sum = sum(heights)
        for i in diffs:
            diff_sum += abs(i)
        return height_sum, diff_sum, max_height, holes

    def get_expected_score_x(self, test_board):
        global weights
        # This function calculates the score of a given board state, given weights and the number of lines previously
        # cleared.
        height_sum, diff_sum, max_height, holes = self.get_parameters_x(test_board)
        A = weights[0]
        B = weights[1]
        C = weights[2]
        D = weights[3]
        test_score = float(A * height_sum + B * diff_sum + C * max_height + D * holes)
        return test_score

    def simulate_board_x(self, test_board, test_piece, move):
        # This function simulates placing the current falling piece onto the
        # board, specified by 'move,' an array with two elements, 'rot' and 'sideways'.
        # 'rot' gives the number of times the piece is to be rotated ranging in [0:3]
        # 'sideways' gives the horizontal movement from the piece's current position, in [-9:9]
        # It removes complete lines and gives returns the next board state as well as the number
        # of lines cleared.

        rot = move[0]
        sideways = move[1]
        test_lines_removed = 0
        reference_height = self.get_parameters_x(test_board)[0]
        if test_piece is None:
            return None

        # Rotate test_piece to match the desired move
        for i in range(0, rot):
            test_piece['rotation'] = (test_piece['rotation'] + 1) % len(PIECES[test_piece['shape']])

        # Test for move validity!
        if not is_valid_position(test_board, test_piece, adj_x=sideways, adj_y=0):
            # The move itself is not valid!
            return None

        # Move the test_piece to collide on the board
        test_piece['x'] += sideways
        for i in range(0, BOARDHEIGHT):
            if is_valid_position(test_board, test_piece, adj_x=0, adj_y=1):
                test_piece['y'] = i

        # Place the piece on the virtual board
        if is_valid_position(test_board, test_piece, adj_x=0, adj_y=0):
            add_to_board(test_board, test_piece)
            test_lines_removed, test_board = remove_complete_lines(test_board)

        height_sum, diff_sum, max_height, holes = self.get_parameters_x(test_board)
        one_step_reward = 5 * (test_lines_removed * test_lines_removed) - (height_sum - reference_height)
        # print("one_step_reward: ",one_step_reward)
        return test_board, one_step_reward

    def find_best_move(self, board, piece):
        move_list = []
        score_list = []
        for rot in range(0, len(PIECES[piece['shape']])):
            for sideways in range(-5, 6):
                move = [rot, sideways]
                test_board = copy.deepcopy(board)
                test_piece = copy.deepcopy(piece)
                test_board = self.simulate_board_x(test_board, test_piece, move)
                if test_board is not None:
                    move_list.append(move)
                    test_score = self.get_expected_score_x(test_board[0])
                    score_list.append(test_score)
        best_score = max(score_list)
        best_move = move_list[score_list.index(best_score)]

        if random.random() < self.explore_change:
            move = move_list[random.randint(0, len(move_list) - 1)]
        else:
            move = best_move
        return move

    def sdg(self, board, piece):
        global weights
        move = self.find_best_move(board, piece)
        old_params = self.get_parameters_x(board)
        test_board = copy.deepcopy(board)
        test_piece = copy.deepcopy(piece)
        test_board = self.simulate_board_x( test_board, test_piece, move)
        if test_board is not None:
            new_params = self.get_parameters_x(test_board[0])
            one_step_reward = test_board[1]
        for i in range(0, len(weights)):
            weights[i] = weights[i] + self.alpha * weights[i] * (one_step_reward - old_params[i] + self.gamma * new_params[i])
        regularization_term = abs(sum(weights))
        for i in range(0, len(weights)):
            weights[i] = 100 * weights[i] / regularization_term
            weights[i] = math.floor(1e4 * weights[i]) / 1e4  # Rounds the weights

        if self.explore_change > 0.001:
            self.explore_change = self.explore_change * 0.99
        else:
            self.explore_change = 0
        #print("byby: ", weights)
        return move


if __name__ == "__main__":
    print("START SDG QL ")
    r_p = sys.argv[1]
    numOfRun = int(sys.argv[2])
    print("globalWeights ",weights)
    for x in range(numOfRun):
        SdgQL = SDG_QL(r_p)
        newScore, _ = SdgQL.run()
        print("Game achieved a score of: ", newScore)
        #print("weights ", SdgQL.weights)