# Keep existing imports
import tkinter as tk
from tkinter import ttk
import os
import pygame.mixer

import math
import random
import copy
import time

# Add MCTS classes here, before the ChineseChess class
class MCTSNode:
    def __init__(self, game, state, parent=None, move=None, color='black'):
        self.game = game        # Reference to the game instance
        self.state = state      # Game state (board configuration)
        self.parent = parent    # Parent node
        self.move = move        # Move that led to this state
        self.color = color      # Color to play in this state
        self.children = []      # Child nodes
        self.wins = 0          # Number of wins from this node
        self.visits = 0        # Number of visits to this node
        self.untried_moves = self._get_valid_moves()  # Moves not yet expanded

    def _get_valid_moves(self):
        """Get all valid moves for the current state"""
        moves = []
        for row in range(10):
            for col in range(9):
                piece = self.state[row][col]
                if piece and piece[0] == self.color[0].upper():
                    for to_row in range(10):
                        for to_col in range(9):
                            if self._is_valid_move((row, col), (to_row, to_col)):
                                moves.append(((row, col), (to_row, to_col)))
        return moves

    def _is_valid_move(self, from_pos, to_pos):
        """Validate moves using the game's validation logic"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.state[from_row][from_col]
        
        if not piece:
            return False
            
        # Basic validation
        if not (0 <= to_row < 10 and 0 <= to_col < 9):
            return False
            
        # Can't capture own pieces
        if self.state[to_row][to_col] and self.state[to_row][to_col][0] == piece[0]:
            return False

        # Use the game's validation methods
        piece_type = piece[1]
        if piece_type in ['帥', '將']:
            return self.game.is_valid_general_move(from_pos, to_pos)
        elif piece_type in ['仕', '士']:
            return self.game.is_valid_advisor_move(from_pos, to_pos)
        elif piece_type in ['相', '象']:
            return self.game.is_valid_elephant_move(from_pos, to_pos)
        elif piece_type == '馬':
            return self.game.is_valid_horse_move(from_pos, to_pos)
        elif piece_type == '車':
            return self.game.is_valid_chariot_move(from_pos, to_pos)
        elif piece_type == '炮':
            return self.game.is_valid_cannon_move(from_pos, to_pos)
        elif piece_type in ['兵', '卒']:
            return self.game.is_valid_pawn_move(from_pos, to_pos)
        return False

    def uct_value(self, exploration_constant):
        """Calculate the UCT value for this node"""
        if self.visits == 0:
            return float('inf')
        return (self.wins / self.visits) + exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)

class MCTS:
    def __init__(self, game, state, color, time_limit=1.0, exploration_constant=1.41):
        self.game = game
        self.root = MCTSNode(game, copy.deepcopy(state), color=color)
        self.time_limit = time_limit
        self.exploration_constant = exploration_constant

    def select_node(self):
        """Select a node to expand using UCT"""
        node = self.root
        while node.untried_moves == [] and node.children:
            node = max(node.children, key=lambda n: n.uct_value(self.exploration_constant))
        return node

    def expand_node(self, node):
        """Expand a node by adding one of its untried moves"""
        if not node.untried_moves:
            return node
            
        move = random.choice(node.untried_moves)
        node.untried_moves.remove(move)
        
        # Create new state
        new_state = copy.deepcopy(node.state)
        from_pos, to_pos = move
        new_state[to_pos[0]][to_pos[1]] = new_state[from_pos[0]][from_pos[1]]
        new_state[from_pos[0]][from_pos[1]] = None
        
        # Create new node
        new_color = 'red' if node.color == 'black' else 'black'
        child = MCTSNode(self.game, new_state, parent=node, move=move, color=new_color)
        node.children.append(child)
        return child

    def simulate(self, node):
        """Simulate a random game from the node's state"""
        state = copy.deepcopy(node.state)
        color = node.color
        moves_count = 0
        max_moves = 50  # Prevent infinite games
        
        while moves_count < max_moves:
            # Get valid moves
            moves = []
            for row in range(10):
                for col in range(9):
                    piece = state[row][col]
                    if piece and piece[0] == color[0].upper():
                        for to_row in range(10):
                            for to_col in range(9):
                                if self.game.is_valid_move((row, col), (to_row, to_col)):
                                    moves.append(((row, col), (to_row, to_col)))
            
            if not moves:
                # Game over - no moves available
                return color != self.root.color  # Win if opponent has no moves
                
            # Make random move
            from_pos, to_pos = random.choice(moves)
            state[to_pos[0]][to_pos[1]] = state[from_pos[0]][from_pos[1]]
            state[from_pos[0]][from_pos[1]] = None
            
            # Check for checkmate
            if self.game.is_checkmate(color):
                return color == self.root.color
                
            color = 'red' if color == 'black' else 'black'
            moves_count += 1
        
        # If no decisive result, evaluate position
        return self._evaluate_position(state, self.root.color) > 0

    def backpropagate(self, node, result):
        """Backpropagate the result through the tree"""
        while node:
            node.visits += 1
            node.wins += result
            node = node.parent

    def get_best_move(self):
        """Get the best move according to the MCTS algorithm"""
        start_time = time.time()
        
        while time.time() - start_time < self.time_limit:
            node = self.select_node()
            node = self.expand_node(node)
            result = self.simulate(node)
            self.backpropagate(node, result)
        
        # Return the move of the most visited child
        if not self.root.children:
            return None
        return max(self.root.children, key=lambda n: n.visits).move

    def _evaluate_position(self, state, color):
        """Simple position evaluation"""
        piece_values = {
            '將': 10000, '帥': 10000,
            '車': 900,
            '馬': 400,
            '炮': 500,
            '象': 200, '相': 200,
            '士': 200, '仕': 200,
            '卒': 100, '兵': 100
        }
        
        score = 0
        for row in range(10):
            for col in range(9):
                piece = state[row][col]
                if piece:
                    value = piece_values[piece[1]]
                    if piece[0] == color[0].upper():
                        score += value
                    else:
                        score -= value
        return score

# Your existing ChineseChess class starts here, but we need to modify the make_ai_move method:

    def make_ai_move(self):
        """Make an AI move using MCTS"""
        if self.is_checkmate('red') or self.is_checkmate('black'):
            self.game_over = True
            return
            
        # Get AI's color based on board orientation
        ai_color = 'red' if self.flipped else 'black'
        
        # Create MCTS instance with reference to the game
        mcts = MCTS(self, self.board, ai_color, time_limit=2.0)
        best_move = mcts.get_best_move()
        
        if not best_move:
            self.game_over = True
            return
            
        from_pos, to_pos = best_move
        moving_piece = self.board[from_pos[0]][from_pos[1]]
        
        # Make the move
        self.board[to_pos[0]][to_pos[1]] = moving_piece
        self.board[from_pos[0]][from_pos[1]] = None
        
        # Play move sound
        if self.sound_effect_on:
            if hasattr(self, 'move_sound') and self.move_sound:
                self.move_sound.play()
                    
        # Update game state
        self.highlighted_positions = [from_pos, to_pos]
        self.add_move_to_records(from_pos, to_pos, moving_piece)
        
        # Switch players
        self.current_player = 'red' if ai_color == 'black' else 'black'
        
        # Handle rotation if needed
        if self.check_rotate:
            self.move_rotate = True
            self.rotate_to_replay()
            from_pos = self.rotate_single_highlight[0]
            to_pos = self.rotate_single_highlight[1]
            
            self.history_top_numbers = []
            self.history_bottom_numbers = []
            
            self.history_top_numbers[:] = self.bottom_numbers[:]
            self.history_bottom_numbers[:] = self.top_numbers[:]
            self.history_top_numbers.reverse()
            self.history_bottom_numbers.reverse()
            
            self.move_history_numbers.append([self.history_top_numbers, self.history_bottom_numbers])
        else:
            self.move_history_numbers.append([self.top_numbers, self.bottom_numbers])
        
        # Add the move to history
        self.add_move_to_history(from_pos, to_pos, moving_piece)
        
        # Update display
        self.draw_board()
        
        # Check for checkmate
        if self.is_checkmate(self.current_player):
            self.handle_game_end()
        else:
            self.game_over = False

# Remove the minimax and related evaluation methods as they're no longer needed:
# - minimax
# - evaluate_position_simple
# - evaluate_checkmate_potential
# - _move_sorting_score