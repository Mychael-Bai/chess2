import random
import math
import copy
from typing import List, Tuple, Optional

class MCTSNode:
    def __init__(self, state, parent=None, move=None, player=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.player = player
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = None
        self.flipped = False

    def simulate(self, node):
        """Simulate a random game from this node"""
        state = copy.deepcopy(node.state)
        current_player = node.player
        depth = 0
        max_depth = 50

        # Add safety evaluation
        def evaluate_move_safety(move, state, player):
            from_pos, to_pos = move
            piece = state[from_pos[0]][from_pos[1]]
            
            # Make move temporarily
            captured = state[to_pos[0]][to_pos[1]]
            state[to_pos[0]][to_pos[1]] = piece
            state[from_pos[0]][from_pos[1]] = None
            
            # Check if piece is under immediate attack
            is_safe = True
            piece_value = self.get_piece_value(piece[1])
            
            for row in range(10):
                for col in range(9):
                    attacking_piece = state[row][col]
                    if attacking_piece and attacking_piece[0] != player[0].upper():
                        if self.is_valid_move((row, col), to_pos):
                            attacker_value = self.get_piece_value(attacking_piece[1])
                            if attacker_value <= piece_value:
                                is_safe = False
                                break
            
            # Restore position
            state[from_pos[0]][from_pos[1]] = piece
            state[to_pos[0]][to_pos[1]] = captured
            
            return is_safe

        while depth < max_depth:
            valid_moves = []
            for row in range(10):
                for col in range(9):
                    piece = state[row][col]
                    if piece and piece[0] == current_player[0].upper():
                        for to_row in range(10):
                            for to_col in range(9):
                                move = ((row, col), (to_row, to_col))
                                if self.is_valid_move(move[0], move[1]):
                                    # Only add safe moves or capturing moves that are favorable
                                    if evaluate_move_safety(move, state, current_player):
                                        valid_moves.append(move)

            if not valid_moves:
                break

            # Choose move with preference for safe ones
            move = random.choice(valid_moves)
            from_pos, to_pos = move
            
            # Make the move
            state[to_pos[0]][to_pos[1]] = state[from_pos[0]][from_pos[1]]
            state[from_pos[0]][from_pos[1]] = None
            
            current_player = 'black' if current_player == 'red' else 'red'
            depth += 1

        # Return result based on final position evaluation
        return self.evaluate_final_position(state, self.player)

    @staticmethod
    def get_piece_value(piece_type):
        """Get the relative value of a piece"""
        values = {
            '將': 1000, '帥': 1000,
            '車': 90,
            '馬': 40,
            '炮': 45,
            '象': 20, '相': 20,
            '士': 20, '仕': 20,
            '卒': 10, '兵': 10
        }
        return values.get(piece_type, 0)

    def evaluate_final_position(self, state, player):
        """Evaluate the final position of the simulation"""
        score = 0
        opponent = 'black' if player == 'red' else 'red'
        
        for row in range(10):
            for col in range(9):
                piece = state[row][col]
                if piece:
                    value = self.get_piece_value(piece[1])
                    if piece[0] == player[0].upper():
                        score += value
                    else:
                        score -= value
        
        return 1 if score > 0 else 0

    def is_valid_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.state[from_row][from_col]
        
        if not (0 <= to_row < 10 and 0 <= to_col < 9):
            return False
            
        if self.state[to_row][to_col] and self.state[to_row][to_col][0] == piece[0]:
            return False
        
        piece_type = piece[1]
        
        if piece_type == '帥' or piece_type == '將':
            return self.is_valid_general_move(from_pos, to_pos)
        elif piece_type == '仕' or piece_type == '士':
            return self.is_valid_advisor_move(from_pos, to_pos)
        elif piece_type == '相' or piece_type == '象':
            return self.is_valid_elephant_move(from_pos, to_pos)
        elif piece_type == '馬':
            return self.is_valid_horse_move(from_pos, to_pos)
        elif piece_type == '車':
            return self.is_valid_chariot_move(from_pos, to_pos)
        elif piece_type == '炮':
            return self.is_valid_cannon_move(from_pos, to_pos)
        elif piece_type == '兵' or piece_type == '卒':
            return self.is_valid_pawn_move(from_pos, to_pos)
        
        return False

    def is_valid_general_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.state[from_row][from_col]
        
        if piece[0] == 'R':
            if not self.flipped:
                if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                    return False
            else:
                if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                    return False
        else:
            if not self.flipped:
                if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                    return False
            else:
                if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                    return False
        
        return abs(to_row - from_row) + abs(to_col - from_col) == 1

    def is_valid_advisor_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.state[from_row][from_col]
        
        if piece[0] == 'R':
            if not self.flipped:
                if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                    return False
            else:
                if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                    return False
        else:
            if not self.flipped:
                if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                    return False
            else:
                if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                    return False
        
        return abs(to_row - from_row) == 1 and abs(to_col - from_col) == 1

    def is_valid_elephant_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.state[from_row][from_col]
        
        if piece[0] == 'R':
            if not self.flipped:
                if to_row < 5:
                    return False
            else:
                if to_row > 4:
                    return False
        else:
            if not self.flipped:
                if to_row > 4:
                    return False
            else:
                if to_row < 5:
                    return False
        
        if abs(to_row - from_row) != 2 or abs(to_col - from_col) != 2:
            return False
        
        blocking_row = (from_row + to_row) // 2
        blocking_col = (from_col + to_col) // 2
        return not self.state[blocking_row][blocking_col]

    def is_valid_horse_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        if not ((row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)):
            return False
        
        if row_diff == 2:
            blocking_row = from_row + (1 if to_row > from_row else -1)
            return not self.state[blocking_row][from_col]
        else:
            blocking_col = from_col + (1 if to_col > from_col else -1)
            return not self.state[from_row][blocking_col]

    def is_valid_chariot_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        if from_row != to_row and from_col != to_col:
            return False
        
        if from_row == to_row:
            start_col = min(from_col, to_col) + 1
            end_col = max(from_col, to_col)
            return not any(self.state[from_row][col] for col in range(start_col, end_col))
        else:
            start_row = min(from_row, to_row) + 1
            end_row = max(from_row, to_row)
            return not any(self.state[row][from_col] for row in range(start_row, end_row))

    def is_valid_cannon_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        if from_row != to_row and from_col != to_col:
            return False
        
        pieces_between = 0
        if from_row == to_row:
            start_col = min(from_col, to_col) + 1
            end_col = max(from_col, to_col)
            pieces_between = sum(1 for col in range(start_col, end_col) if self.state[from_row][col])
        else:
            start_row = min(from_row, to_row) + 1
            end_row = max(from_row, to_row)
            pieces_between = sum(1 for row in range(start_row, end_row) if self.state[row][from_col])
        
        return pieces_between == 1 if self.state[to_row][to_col] else pieces_between == 0

    def is_valid_pawn_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.state[from_row][from_col]
        
        if piece[0] == 'R':
            if not self.flipped:
                if from_row > 4:
                    return to_col == from_col and to_row == from_row - 1
                else:
                    return (to_col == from_col and to_row == from_row - 1) or \
                           (to_row == from_row and abs(to_col - from_col) == 1)
            else:
                if from_row < 5:
                    return to_col == from_col and to_row == from_row + 1
                else:
                    return (to_col == from_col and to_row == from_row + 1) or \
                           (to_row == from_row and abs(to_col - from_col) == 1)
        else:
            if not self.flipped:
                if from_row < 5:
                    return to_col == from_col and to_row == from_row + 1
                else:
                    return (to_col == from_col and to_row == from_row + 1) or \
                           (to_row == from_row and abs(to_col - from_col) == 1)
            else:
                if from_row > 4:
                    return to_col == from_col and to_row == from_row - 1
                else:
                    return (to_col == from_col and to_row == from_row - 1) or \
                           (to_row == from_row and abs(to_col - from_col) == 1)

    def UCB1(self, exploration_constant=1.414):
        """Calculate the UCB1 value for this node"""
        if self.visits == 0:
            return float('inf')
        if not self.parent:
            return float('-inf')
        return (self.wins / self.visits) + exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)

    def get_untried_moves(self):
        """Get list of untried moves from this state"""
        if self.untried_moves is None:
            self.untried_moves = []
            for row in range(10):
                for col in range(9):
                    piece = self.state[row][col]
                    if piece and piece[0] == self.player[0].upper():
                        for to_row in range(10):
                            for to_col in range(9):
                                if self.is_valid_move((row, col), (to_row, to_col)):
                                    self.untried_moves.append(((row, col), (to_row, to_col)))
        return self.untried_moves

    def select_child(self):
        """Select the child with the highest UCB1 value"""
        return max(self.children, key=lambda c: c.UCB1())

class MCTS:
    def __init__(self, initial_state, player, iterations=1000):
        self.root = MCTSNode(initial_state, player=player)
        self.iterations = iterations

    def select(self):
        node = self.root
        # Use get_untried_moves instead of get_valid_moves
        while node.get_untried_moves() == [] and node.children:
            node = max(node.children, key=lambda n: n.UCB1())
        return node

    def expand(self, node):
        moves = node.get_untried_moves()
        if not moves:
            return None
            
        move = random.choice(moves)
        node.untried_moves.remove(move)
        
        # Create new state
        new_state = copy.deepcopy(node.state)
        from_pos, to_pos = move
        new_state[to_pos[0]][to_pos[1]] = new_state[from_pos[0]][from_pos[1]]
        new_state[from_pos[0]][from_pos[1]] = None
        
        # Switch player
        new_player = 'black' if node.player == 'red' else 'red'
        child = MCTSNode(new_state, parent=node, move=move, player=new_player)
        node.children.append(child)
        return child

    def simulate(self, node):
        state = copy.deepcopy(node.state)
        current_player = node.player
        
        # Simulate random moves until game end or max depth
        max_depth = 50
        depth = 0
        
        while depth < max_depth:
            # Get all valid moves for current player
            valid_moves = []
            for row in range(10):
                for col in range(9):
                    piece = state[row][col]
                    if piece and piece[0] == current_player[0].upper():
                        for to_row in range(10):
                            for to_col in range(9):
                                if self.is_valid_move(state, (row, col), (to_row, to_col)):
                                    valid_moves.append(((row, col), (to_row, to_col)))
            
            if not valid_moves:
                break
                
            # Make random move
            from_pos, to_pos = random.choice(valid_moves)
            state[to_pos[0]][to_pos[1]] = state[from_pos[0]][from_pos[1]]
            state[from_pos[0]][from_pos[1]] = None
            
            current_player = 'black' if current_player == 'red' else 'red'
            depth += 1
        
        # Return 1 for win, 0 for loss
        return 1 if current_player != self.root.player else 0

    def backpropagate(self, node, result):
        while node:
            node.visits += 1
            node.wins += result
            node = node.parent
            result = 1 - result



    def find_kings(self):
        """Find positions of both kings on the board"""
        red_king_pos = None
        black_king_pos = None
        
        for row in range(10):
            for col in range(9):
                piece = self.root.state[row][col]
                if piece:
                    if piece == 'R帥':
                        red_king_pos = (row, col)
                    elif piece == 'B將':
                        black_king_pos = (row, col)
                        
        return red_king_pos, black_king_pos

    def is_generals_facing(self):
        """Check if the two generals are facing each other"""
        red_king_pos, black_king_pos = self.find_kings()
        
        if not (red_king_pos and black_king_pos):
            return False
            
        if red_king_pos[1] != black_king_pos[1]:
            return False
            
        # Check if there are any pieces between the generals
        col = red_king_pos[1]
        start_row = min(red_king_pos[0], black_king_pos[0]) + 1
        end_row = max(red_king_pos[0], black_king_pos[0])
        
        return not any(self.root.state[row][col] for row in range(start_row, end_row))

    def is_position_under_attack(self, pos, by_player):
        """Check if a position is under attack by the specified player"""
        for row in range(10):
            for col in range(9):
                piece = self.root.state[row][col]
                if piece and piece[0] == by_player[0].upper():
                    if self.root.is_valid_move((row, col), pos):
                        return True
        return False

    def is_in_check(self, color):
        """Check if the king of the given color is in check"""
        red_king_pos, black_king_pos = self.find_kings()
        
        if not red_king_pos or not black_king_pos:
            return False
        
        # First check the special case of facing generals
        if self.is_generals_facing():
            return True  # Both kings are in check in this case
        
        # Then check the normal cases of being under attack
        if color == 'red':
            return self.is_position_under_attack(red_king_pos, 'black')
        else:
            return self.is_position_under_attack(black_king_pos, 'red')

    def get_best_move(self):
        for _ in range(self.iterations):
            node = self.select()
            child = self.expand(node)
            if child:
                # Create a temporary state to test if the move puts us in check
                test_state = copy.deepcopy(self.root.state)
                from_pos, to_pos = child.move
                test_state[to_pos[0]][to_pos[1]] = test_state[from_pos[0]][from_pos[1]]
                test_state[from_pos[0]][from_pos[1]] = None
                
                # Check if our move puts our own king in check
                if not self.is_in_check(self.root.player):
                    result = self.simulate(child)
                    self.backpropagate(child, result)
            else:
                result = self.simulate(node)
                self.backpropagate(node, result)

        if not self.root.children:
            # Fallback to random valid move if no good moves found
            valid_moves = []
            for row in range(10):
                for col in range(9):
                    piece = self.root.state[row][col]
                    if piece and piece[0] == self.root.player[0].upper():
                        for to_row in range(10):
                            for to_col in range(9):
                                move = ((row, col), (to_row, to_col))
                                if self.root.is_valid_move(move[0], move[1]):
                                    # Test if move doesn't leave us in check
                                    test_state = copy.deepcopy(self.root.state)
                                    test_state[to_row][to_col] = test_state[row][col]
                                    test_state[row][col] = None
                                    if not self.is_in_check(self.root.player):
                                        valid_moves.append(move)
            return random.choice(valid_moves) if valid_moves else None

        # Return the move with the highest visit count
        best_child = max(self.root.children, key=lambda c: c.visits)
        return best_child.move


    @staticmethod
    def is_valid_move(state, from_pos, to_pos):
        # Copy the move validation logic from MCTSNode class
        # This is a simplified version for simulation
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = state[from_row][from_col]
        
        if not (0 <= to_row < 10 and 0 <= to_col < 9):
            return False
            
        if state[to_row][to_col] and state[to_row][to_col][0] == piece[0]:
            return False
            
        return True