
import tkinter as tk
from tkinter import ttk
import os
import pygame.mixer

import math
import random
import copy
import time

# fixed the checkmate method, this version is derived from 7.3.50


# --- Piece Values (Tunable) ---
PIECE_VALUES = {
    # Use positive values, sign will be determined by color
    '將': 10000, '帥': 10000,
    '車': 900,
    '馬': 400,
    '炮': 450,  # Slightly different from Horse
    '象': 200, '相': 200,
    '士': 200, '仕': 200,
    '卒': 100, '兵': 100
}
# Bonus for pawns crossing the river
PAWN_ACROSS_RIVER_BONUS_MG = 80  # Middlegame
PAWN_ACROSS_RIVER_BONUS_EG = 120 # Endgame

# --- Evaluation Weights (Tunable) ---
MATERIAL_WEIGHT = 1.0
PST_WEIGHT = 0.1       # Position value weight
MOBILITY_WEIGHT = 0.05   # Mobility weight
KING_SAFETY_WEIGHT = 0.15 # King safety weight
CONNECTED_DEFENDERS_WEIGHT = 0.05 # Bonus for connected Advisors/Elephants

# --- Piece Square Tables (PSTs) ---
# Values represent bonuses/penalties for a piece being on that square.
# Indexed by [row][col]. Needs careful flipping logic.
# These are EXAMPLE values - Tuning is essential!

# Note: Define tables from Black's perspective (row 0 is Black's baseline)
# We will flip the row index for Red pieces or when the board is flipped.

# King (General) - Restricted to Palace
# fmt: off
KING_PST_BLACK = [
    [ 0,  0,  0,  5,  8,  5,  0,  0,  0],
    [ 0,  0,  0,  5,  5,  5,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0], # Red Palace Area (Irrelevant for Black King PST)
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0]
]

# Advisor - Restricted to Palace
ADVISOR_PST_BLACK = [
    [ 0,  0,  0,  5,  0,  5,  0,  0,  0],
    [ 0,  0,  0,  0, 10,  0,  0,  0,  0],
    [ 0,  0,  0,  5,  0,  5,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0]
]

# Elephant - Restricted to own side, cannot cross river
ELEPHANT_PST_BLACK = [
    [ 0,  0,  5,  0,  0,  0,  5,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 5,  0,  0,  0, 10,  0,  0,  0,  5],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  5,  0,  0,  0,  5,  0,  0],
    [-5, -5, -5, -5, -5, -5, -5, -5, -5], # Penalty if somehow crossed river (shouldn't happen)
    [-5, -5, -5, -5, -5, -5, -5, -5, -5],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0], # Red Area (Irrelevant for Black Elephant PST)
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0]
]

# Horse
HORSE_PST = [
    [ 0, -3,  0,  0,  0,  0,  0, -3,  0],
    [ 0,  0,  5,  5,  8,  5,  5,  0,  0],
    [ 0,  5, 10, 12, 15, 12, 10,  5,  0],
    [ 5,  8, 12, 15, 18, 15, 12,  8,  5],
    [ 5, 10, 12, 16, 15, 16, 12, 10,  5],
    [ 5,  8, 10, 15, 12, 15, 10,  8,  5],
    [ 0,  5,  8, 10, 10, 10,  8,  5,  0],
    [ 0,  0,  4,  5,  5,  5,  4,  0,  0],
    [ 0, -5,  0,  0,  0,  0,  0, -5,  0],
    [-5,-10, -5, -5, -5, -5, -5,-10, -5]
]

# Rook (Chariot)
ROOK_PST = [
    [ 10, 10, 10, 12, 12, 12, 10, 10, 10],
    [ 12, 15, 14, 16, 16, 16, 14, 15, 12],
    [ 12, 14, 12, 15, 15, 15, 12, 14, 12],
    [ 12, 15, 12, 16, 16, 16, 12, 15, 12],
    [ 12, 12, 12, 14, 14, 14, 12, 12, 12],
    [ 10, 10, 10, 12, 12, 12, 10, 10, 10], # River
    [ 8,  8,  8, 10, 10, 10,  8,  8,  8],
    [ 6,  6,  6,  8,  8,  8,  6,  6,  6],
    [ 4,  4,  4,  6,  6,  6,  4,  4,  4],
    [ 0,  0,  0,  5,  0,  5,  0,  0,  0]
]

# Cannon
CANNON_PST = [
    [ 5,  5,  5,  5,  5,  5,  5,  5,  5],
    [ 4,  4,  4,  8, 10,  8,  4,  4,  4],
    [ 4,  4,  4,  8,  8,  8,  4,  4,  4],
    [ 6,  8,  8,  8,  8,  8,  8,  8,  6],
    [ 8,  8,  8,  8,  8,  8,  8,  8,  8],
    [ 8,  8, 10, 10, 10, 10, 10,  8,  8], # Slightly better near center and enemy lines
    [10, 10, 10, 12, 12, 12, 10, 10, 10],
    [10, 10, 10, 10, 10, 10, 10, 10, 10],
    [ 8,  8,  8,  8,  8,  8,  8,  8,  8],
    [ 5,  5,  5,  5,  5,  5,  5,  5,  5]
]

# Pawn (Soldier) - Needs special handling for crossing the river
PAWN_PST = [
    [ 0,  0,  0, 20, 25, 20,  0,  0,  0], # Enemy baseline - very valuable
    [ 0,  0,  0, 15, 18, 15,  0,  0,  0],
    [ 0,  0,  0, 12, 15, 12,  0,  0,  0],
    [ 0,  0,  0, 10, 12, 10,  0,  0,  0],
    [ 5,  5,  8,  8, 10,  8,  8,  5,  5], # Just across river
    [ 5,  5,  5,  5,  5,  5,  5,  5,  5], # On river line
    [ 2,  2,  2,  3,  3,  3,  2,  2,  2], # Before river
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0]
]
# fmt: on

# --- Combine PSTs into a dictionary ---
# We'll use specific PSTs for Black's palace pieces and general ones for others
# The get_pst_score function will handle color and flipping.
PST = {
    '將': KING_PST_BLACK,
    '士': ADVISOR_PST_BLACK,
    '象': ELEPHANT_PST_BLACK,
    '帥': KING_PST_BLACK,   # Will be flipped
    '仕': ADVISOR_PST_BLACK, # Will be flipped
    '相': ELEPHANT_PST_BLACK,# Will be flipped
    '馬': HORSE_PST,
    '車': ROOK_PST,
    '炮': CANNON_PST,
    '卒': PAWN_PST,
    '兵': PAWN_PST         # Will be flipped
}

# --- Helper Functions ---

def _determine_game_phase(state):
    """ Estimate game phase (0.0 = opening, 1.0 = endgame) based on material """
    max_material_approx = 2 * (PIECE_VALUES['車'] * 2 + PIECE_VALUES['馬'] * 2 + PIECE_VALUES['炮'] * 2 + \
                             PIECE_VALUES['相'] * 2 + PIECE_VALUES['仕'] * 2 + PIECE_VALUES['兵'] * 5)
    current_material = 0
    for r in range(10):
        for c in range(9):
            piece = state[r][c]
            if piece and piece[1] not in '帥將': # Exclude kings from phase calc
                current_material += PIECE_VALUES[piece[1]]

    # Normalize phase (simplified): Linear decay based on material remaining
    phase = max(0.0, 1.0 - (current_material / (max_material_approx * 0.7))) # Consider midgame starts early
    return phase

def get_pst_score(piece_type, piece_color, r, c, flipped):
    """ Gets the PST score considering piece, color, and board flip status """
    pst_table = PST[piece_type]

    # Determine the correct row and column for PST lookup
    lookup_r, lookup_c = r, c

    if piece_color == 'R':
        # Red's baseline is row 9. Flip row index.
        lookup_r = 9 - r
        # If board is flipped, Red is now at the top, flip both row and col
        if flipped:
            lookup_r = r # Equivalent to 9 - (9 - r)
            lookup_c = 8 - c
    else: # Black piece
        # Black's baseline is row 0.
        # If board is flipped, Black is now at the bottom, flip both row and col
        if flipped:
            lookup_r = 9 - r
            lookup_c = 8 - c

    # Ensure indices are within bounds (shouldn't be necessary with valid moves, but safe)
    lookup_r = max(0, min(9, lookup_r))
    lookup_c = max(0, min(8, lookup_c))

    return pst_table[lookup_r][lookup_c]

def _get_piece_mobility(validator, state, from_pos, piece_color):
    """ Calculates the number of *legal* moves for a piece """
    mobility = 0
    from_r, from_c = from_pos
    piece = state[from_r][from_c]
    if not piece: return 0

    original_board = validator.board # Remember original validator board ref
    validator.board = state # Point validator to current state for this calc

    for to_r in range(10):
        for to_c in range(9):
            to_pos = (to_r, to_c)
            if validator.is_valid_move(from_pos, to_pos):
                # Test if the move is legal (doesn't leave king in check)
                target_piece = state[to_r][to_c]
                state[to_r][to_c] = piece
                state[from_r][from_c] = None

                # Check if the king of the moving color is now in check
                in_check_after_move = validator.is_in_check(piece_color)

                # Undo the move on the temporary state
                state[from_r][from_c] = piece
                state[to_r][to_c] = target_piece

                if not in_check_after_move:
                    mobility += 1

    validator.board = original_board # Restore validator board reference
    return mobility

def _evaluate_king_safety(validator, state, king_pos, king_color, flipped):
    """ Basic King Safety Evaluation """
    if not king_pos: return -10000 # King captured? Should not happen in eval

    safety_score = 0
    king_r, king_c = king_pos
    opponent_color = 'black' if king_color == 'red' else 'red'

    # 1. Pawn Shield Penalty (Simplified: check pawn directly in front)
    shield_r = king_r - 1 if (king_color == 'red' and not flipped) or (king_color == 'black' and flipped) else king_r + 1
    if 0 <= shield_r < 10:
        # Penalize if the pawn in front is missing, less penalty if king is not on center file
        center_files = [3, 4, 5]
        penalty_multiplier = 1.5 if king_c in center_files else 1.0
        pawn_type = '兵' if king_color == 'red' else '卒'
        if state[shield_r][king_c] is None or state[shield_r][king_c][1] != pawn_type:
             safety_score -= 30 * penalty_multiplier
        # Small bonus if pawn is present
        elif state[shield_r][king_c] and state[shield_r][king_c][1] == pawn_type:
             safety_score += 5 * penalty_multiplier


    # 2. Attacker Count/Proximity (Simplified: check squares around king)
    attack_zone = []
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
             # Also check 2 steps for cannons/rooks/horses potential
            for dist in [1, 2]:
                nr, nc = king_r + dr * dist, king_c + dc * dist
                if 0 <= nr < 10 and 0 <= nc < 9:
                    if (nr, nc) not in attack_zone:
                        attack_zone.append((nr, nc))
    if king_pos not in attack_zone: attack_zone.append(king_pos) # Include king's square

    num_attackers = 0
    attacker_value_sum = 0

    original_board = validator.board
    validator.board = state
    for r in range(10):
        for c in range(9):
            piece = state[r][c]
            if piece and piece[0] == opponent_color[0].upper():
                # Check if this opponent piece attacks any square in the king's zone
                for zone_r, zone_c in attack_zone:
                    if validator.is_valid_move((r, c), (zone_r, zone_c)):
                        num_attackers += 1
                        attacker_value_sum += PIECE_VALUES[piece[1]] // 10 # Scaled value
                        break # Count each attacker only once

    validator.board = original_board

    # Penalties based on attackers
    if num_attackers == 1:
        safety_score -= attacker_value_sum // 2
    elif num_attackers >= 2:
        safety_score -= attacker_value_sum # Heavier penalty for multiple attackers

    # 3. Check Penalty (already handled separately, but could add slight extra here)
    # if validator.is_in_check(king_color):
    #    safety_score -= 50 # Small additional penalty if needed

    return safety_score

def _evaluate_structure(state, flipped):
    """ Evaluate structural bonuses/penalties """
    red_structure_score = 0
    black_structure_score = 0

    # Connected Advisors/Elephants Bonus
    # Check standard defensive positions
    # Need to handle flipped board!

    # Define standard positions (relative to baseline)
    advisor_pos = [(0,3), (0,5), (1,4), (2,3), (2,5)] # Black baseline relative
    elephant_pos = [(0,2), (0,6), (2,0), (2,4), (2,8), (4,2), (4,6)] # Black baseline relative

    def check_connected(color_char, piece_char, standard_pos):
        score = 0
        positions = []
        # Find all pieces of this type/color
        for r in range(10):
            for c in range(9):
                piece = state[r][c]
                if piece and piece[0] == color_char and piece[1] == piece_char:
                    positions.append((r, c))

        if len(positions) == 2:
            p1_r, p1_c = positions[0]
            p2_r, p2_c = positions[1]

            # Convert to baseline relative coords for comparison
            is_red = color_char == 'R'
            if is_red:
                rel_p1_r, rel_p1_c = (9-p1_r, p1_c) if not flipped else (p1_r, 8-p1_c)
                rel_p2_r, rel_p2_c = (9-p2_r, p2_c) if not flipped else (p2_r, 8-p2_c)
            else: # Black
                rel_p1_r, rel_p1_c = (p1_r, p1_c) if not flipped else (9-p1_r, 8-p1_c)
                rel_p2_r, rel_p2_c = (p2_r, p2_c) if not flipped else (9-p2_r, 8-p2_c)

            # Check if they occupy standard connected positions
            pos1_valid = (rel_p1_r, rel_p1_c) in standard_pos
            pos2_valid = (rel_p2_r, rel_p2_c) in standard_pos

            if pos1_valid and pos2_valid:
                # Check for connection (specific to advisors/elephants)
                if piece_char in ['仕', '士']: # Advisors connect through center
                     if (rel_p1_r, rel_p1_c) == (1,4) or (rel_p2_r, rel_p2_c) == (1,4):
                         score += 15 # Bonus if one is central
                     else: score += 10
                elif piece_char in ['相', '象']: # Elephants "connect" if they defend each other's blocking points
                    # Simplified: just give bonus if both are on valid squares
                    score += 10

        return score

    red_structure_score += check_connected('R', '仕', advisor_pos)
    red_structure_score += check_connected('R', '相', elephant_pos)
    black_structure_score += check_connected('B', '士', advisor_pos)
    black_structure_score += check_connected('B', '象', elephant_pos)

    return red_structure_score, black_structure_score


# --- Need the supporting classes (ChessValidator, MCTSNode) as in your original file ---
# Make sure ChessValidator is defined correctly and handles flipped state properly in its methods.

class ChessValidator:
    """A lightweight class for chess move validation without GUI components"""
    def __init__(self, board, flipped=False):
        self.game_over = False
        self.board = board # Use the passed board directly
        self.flipped = flipped

    # ... [ COPY ALL VALIDATION METHODS from your original file here ] ...
    # find_kings, is_position_under_attack, is_generals_facing, is_in_check,
    # is_checkmate, is_valid_move, is_valid_general_move, is_valid_advisor_move,
    # is_valid_elephant_move, is_valid_horse_move, is_valid_chariot_move,
    # is_valid_cannon_move, is_valid_pawn_move

    # --- PASTE ChessValidator methods here ---
    def find_kings(self):
        """Find positions of both kings/generals"""
        red_king_pos = black_king_pos = None
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece:
                    if piece[1] == '帥':
                        red_king_pos = (row, col)
                    elif piece[1] == '將':
                        black_king_pos = (row, col)
        return red_king_pos, black_king_pos

    def is_position_under_attack(self, pos, attacking_color):
        """Check if a position is under attack by pieces of the given color"""
        # Check from all positions on the board
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece and piece[0] == attacking_color[0].upper():
                    # Check if this piece can move to the target position
                    # Need a temporary validator instance with the correct board state if is_valid_move modifies self.board
                    # Assuming is_valid_move is read-only w.r.t self.board state
                    if self.is_valid_move((row, col), pos):
                        return True
        return False

    def is_generals_facing(self):
        """Check if the two generals are facing each other directly"""
        red_king_pos, black_king_pos = self.find_kings()

        if not red_king_pos or not black_king_pos:
            return False

        red_row, red_col = red_king_pos
        black_row, black_col = black_king_pos

        if red_col != black_col:
            return False

        start_row = min(red_row, black_row) + 1
        end_row = max(red_row, black_row)

        for row in range(start_row, end_row):
            if self.board[row][red_col]:
                return False

        return True

    def is_in_check(self, color):
        """Check if the king of the given color is in check"""
        red_king_pos, black_king_pos = self.find_kings()

        # Handle case where a king might be missing during evaluation of hypothetical states
        if color == 'red' and not red_king_pos: return False
        if color == 'black' and not black_king_pos: return False
        if not red_king_pos or not black_king_pos: return False # If either is missing, but we're checking the present one

        # Check facing generals first ONLY if both kings are present
        if red_king_pos and black_king_pos and self.is_generals_facing():
            return True

        # Check normal attacks
        if color == 'red':
            return self.is_position_under_attack(red_king_pos, 'black')
        else: # color == 'black'
            return self.is_position_under_attack(black_king_pos, 'red')

    def is_checkmate(self, color):
        """
        Check if the given color is in checkmate.
        Returns True if the player is in check and has no legal moves.
        """
        
        # Check if any move escapes check
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece and piece[0] == color[0].upper():
                    for to_row in range(10):
                        for to_col in range(9):
                            from_pos = (row, col)
                            to_pos = (to_row, to_col)
                            if self.is_valid_move(from_pos, to_pos):
                                # Simulate the move
                                original_piece_at_to = self.board[to_row][to_col]
                                self.board[to_row][to_col] = piece
                                self.board[row][col] = None

                                # Check if still in check
                                still_in_check = self.is_in_check(color)

                                # Undo the move
                                self.board[row][col] = piece
                                self.board[to_row][to_col] = original_piece_at_to

                                if not still_in_check:
                                    return False # Found a legal move

        # If no legal move escapes check, it's checkmate
        self.game_over = True # Set game over flag
        return True


    def is_valid_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]

        if not piece: # Added check if piece exists
            return False

        # Basic validation
        if not (0 <= to_row < 10 and 0 <= to_col < 9):
            return False

        # Can't capture own pieces
        target_piece = self.board[to_row][to_col]
        if target_piece and target_piece[0] == piece[0]:
            return False

        # Get piece type
        piece_type = piece[1]

        # Check specific piece movement rules
        if piece_type in ['帥', '將']:
            return self.is_valid_general_move(from_pos, to_pos)
        elif piece_type in ['仕', '士']:
            return self.is_valid_advisor_move(from_pos, to_pos)
        elif piece_type in ['相', '象']:
            return self.is_valid_elephant_move(from_pos, to_pos)
        elif piece_type == '馬':
            return self.is_valid_horse_move(from_pos, to_pos)
        elif piece_type == '車':
            return self.is_valid_chariot_move(from_pos, to_pos)
        elif piece_type == '炮':
            return self.is_valid_cannon_move(from_pos, to_pos)
        elif piece_type in ['兵', '卒']:
            return self.is_valid_pawn_move(from_pos, to_pos)

        return False

    def is_valid_general_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]

        # Palace check based on flipped status
        is_red = piece[0] == 'R'
        in_palace = False
        if not self.flipped:
            if is_red and (7 <= to_row <= 9 and 3 <= to_col <= 5): in_palace = True
            if not is_red and (0 <= to_row <= 2 and 3 <= to_col <= 5): in_palace = True
        else: # Flipped
            if is_red and (0 <= to_row <= 2 and 3 <= to_col <= 5): in_palace = True
            if not is_red and (7 <= to_row <= 9 and 3 <= to_col <= 5): in_palace = True

        if not in_palace:
            return False

        # Check move distance
        if abs(to_row - from_row) + abs(to_col - from_col) != 1:
            return False

        # Check facing generals rule
        # Temporarily make the move to check if generals face AFTER the move
        target_piece = self.board[to_row][to_col]
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        generals_face = self.is_generals_facing()
        # Undo move
        self.board[from_row][from_col] = piece
        self.board[to_row][to_col] = target_piece

        if generals_face:
             return False # Cannot move into a position where generals face

        return True

    def is_valid_advisor_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]

        # Palace check based on flipped status
        is_red = piece[0] == 'R'
        in_palace = False
        if not self.flipped:
            if is_red and (7 <= to_row <= 9 and 3 <= to_col <= 5): in_palace = True
            if not is_red and (0 <= to_row <= 2 and 3 <= to_col <= 5): in_palace = True
        else: # Flipped
            if is_red and (0 <= to_row <= 2 and 3 <= to_col <= 5): in_palace = True
            if not is_red and (7 <= to_row <= 9 and 3 <= to_col <= 5): in_palace = True

        if not in_palace:
            return False

        # Must move exactly one step diagonally
        if abs(to_row - from_row) != 1 or abs(to_col - from_col) != 1:
            return False

        return True

    def is_valid_elephant_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]

        # River crossing check based on flipped status
        is_red = piece[0] == 'R'
        crossed_river = False
        if not self.flipped:
            if is_red and to_row < 5: crossed_river = True
            if not is_red and to_row > 4: crossed_river = True
        else: # Flipped
            if is_red and to_row > 4: crossed_river = True
            if not is_red and to_row < 5: crossed_river = True

        if crossed_river:
            return False

        # Must move exactly two steps diagonally
        if abs(to_row - from_row) != 2 or abs(to_col - from_col) != 2:
            return False

        # Check blocking piece ("elephant eye")
        blocking_row = (from_row + to_row) // 2
        blocking_col = (from_col + to_col) // 2
        if self.board[blocking_row][blocking_col]:
            return False

        return True

    def is_valid_horse_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        if not ((row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)):
            return False

        # Check blocking piece ("horse leg")
        if row_diff == 2:
            blocking_row = from_row + (1 if to_row > from_row else -1)
            if self.board[blocking_row][from_col]:
                return False
        else: # col_diff == 2
            blocking_col = from_col + (1 if to_col > from_col else -1)
            if self.board[from_row][blocking_col]:
                return False

        return True

    def is_valid_chariot_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        if from_row != to_row and from_col != to_col:
            return False

        # Check path clear
        if from_row == to_row: # Horizontal
            start_col = min(from_col, to_col) + 1
            end_col = max(from_col, to_col)
            for col in range(start_col, end_col):
                if self.board[from_row][col]:
                    return False
        else: # Vertical
            start_row = min(from_row, to_row) + 1
            end_row = max(from_row, to_row)
            for row in range(start_row, end_row):
                if self.board[row][from_col]:
                    return False

        return True

    def is_valid_cannon_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        if from_row != to_row and from_col != to_col:
            return False

        # Count pieces between
        pieces_between = 0
        if from_row == to_row: # Horizontal
            start_col = min(from_col, to_col) + 1
            end_col = max(from_col, to_col)
            for col in range(start_col, end_col):
                if self.board[from_row][col]:
                    pieces_between += 1
        else: # Vertical
            start_row = min(from_row, to_row) + 1
            end_row = max(from_row, to_row)
            for row in range(start_row, end_row):
                if self.board[row][from_col]:
                    pieces_between += 1

        # If capturing, need exactly one piece (screen)
        if self.board[to_row][to_col]:
            return pieces_between == 1
        # If moving without capturing, path must be clear
        else:
            return pieces_between == 0

    def is_valid_pawn_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        is_red = piece[0] == 'R'

        if not self.flipped:
            # Red moves up (decreasing row index)
            if is_red:
                if from_row > 4: # Before river
                    return to_col == from_col and to_row == from_row - 1
                else: # After river
                    return (to_col == from_col and to_row == from_row - 1) or \
                           (to_row == from_row and abs(to_col - from_col) == 1)
            # Black moves down (increasing row index)
            else:
                if from_row < 5: # Before river
                    return to_col == from_col and to_row == from_row + 1
                else: # After river
                    return (to_col == from_col and to_row == from_row + 1) or \
                           (to_row == from_row and abs(to_col - from_col) == 1)
        else: # Flipped board
            # Red moves down (increasing row index)
            if is_red:
                if from_row < 5: # Before river (relative to flipped board)
                    return to_col == from_col and to_row == from_row + 1
                else: # After river
                    return (to_col == from_col and to_row == from_row + 1) or \
                           (to_row == from_row and abs(to_col - from_col) == 1)
            # Black moves up (decreasing row index)
            else:
                if from_row > 4: # Before river (relative to flipped board)
                    return to_col == from_col and to_row == from_row - 1
                else: # After river
                    return (to_col == from_col and to_row == from_row - 1) or \
                           (to_row == from_row and abs(to_col - from_col) == 1)


class MCTSNode:
    # Make sure it correctly initializes the validator with the flipped status
    def __init__(self, state, parent=None, move=None, color='black', flipped=False):
        self.state = state      # The state is already a copy when passed to MCTSNode
        self.parent = parent
        self.move = move
        self.color = color
        self.children = []
        self.wins = 0
        self.visits = 0
        # Create validator with the state directly, ensuring flipped status is passed
        self.validator = ChessValidator(self.state, flipped) # Pass flipped status
        self.untried_moves = self._get_valid_moves(color)

        # Store root reference for AI color comparison and flipped status access
        self.root = self if parent is None else parent.root

    # Ensure _get_valid_moves uses self.validator correctly
    def _get_valid_moves(self, color=None):
        moves = []
        current_color = color if color else self.color
        # Make sure validator uses the node's state
        original_board = self.validator.board
        self.validator.board = self.state

        for row in range(10):
            for col in range(9):
                piece = self.state[row][col]
                if piece and piece[0] == current_color[0].upper():
                    for to_row in range(10):
                        for to_col in range(9):
                            from_pos = (row, col)
                            to_pos = (to_row, to_col)
                            if self.validator.is_valid_move(from_pos, to_pos):
                                # Test if move would result in check for the moving player
                                original_piece_at_to = self.state[to_row][to_col]
                                self.state[to_row][to_col] = piece
                                self.state[row][col] = None

                                # Use the validator (already pointing to self.state)
                                still_in_check = self.validator.is_in_check(current_color)

                                # Undo move on the state
                                self.state[row][col] = piece
                                self.state[to_row][to_col] = original_piece_at_to

                                if not still_in_check:
                                    moves.append((from_pos, to_pos))

        # Restore validator's original board if necessary (though it might not matter if validator is recreated often)
        # self.validator.board = original_board # Probably not needed if validator state isn't reused across nodes directly

        return moves

    # UCT Value calculation might need access to flipped status if heuristics depend on it.
    def uct_value(self, exploration_constant, k=0.1):
        """Calculate UCT value with a distance-based heuristic for AI moves."""
        if self.visits == 0:
            return float('inf')
        # Standard UCT formula
        uct = (self.wins / self.visits) + exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)
        # Apply heuristic only for AI's moves
        if self.parent and self.parent.color == self.root.color and self.move:  # Check parent exists
            # Temporarily set validator to parent's state to find king pos before the move
            original_board = self.validator.board
            self.validator.board = self.parent.state # Use parent state for king pos before move
            self.validator.flipped = self.root.validator.flipped # Ensure flipped status is correct

            # Find opponent's king position
            opponent_king_idx = 1 if self.root.color == 'red' else 0
            kings = self.validator.find_kings()
            opponent_king_pos = kings[opponent_king_idx] if len(kings) > opponent_king_idx else None

            self.validator.board = original_board # Restore validator board

            if opponent_king_pos:
                from_pos, to_pos = self.move
                dist_from = abs(from_pos[0] - opponent_king_pos[0]) + abs(from_pos[1] - opponent_king_pos[1])
                dist_to = abs(to_pos[0] - opponent_king_pos[0]) + abs(to_pos[1] - opponent_king_pos[1])
                delta_dist = dist_to - dist_from
                uct += k * (-delta_dist)  # Bonus for moving closer, penalty for moving away
        return uct


# --- Main Evaluation Function ---

class MCTS:

    def __init__(self, state, color, time_limit=1.0, exploration_constant=1.41, flipped=False, max_mate_depth=2):
        self.root = MCTSNode(copy.deepcopy(state), color=color, flipped=flipped)
        self.time_limit = time_limit
        self.exploration_constant = exploration_constant
        self.max_mate_depth = max_mate_depth
        self.untried_moves = self.root._get_valid_moves(color)  # Moves not yet expanded

        # Ensure validator uses the flipped status from the root
        self.validator = ChessValidator(self.root.state, self.root.validator.flipped)
        self.forced_sequence = None  # To store the checkmate sequence

        self.mate_transposition_table = {}
        # Zobrist initialization
        self.zobrist_table = {}
        piece_types = ['R帥', 'R仕', 'R相', 'R馬', 'R車', 'R炮', 'R兵',
                       'B將', 'B士', 'B象', 'B馬', 'B車', 'B炮', 'B卒']
        for row in range(10):
            for col in range(9):
                for piece in piece_types:
                    self.zobrist_table[(row, col, piece)] = random.getrandbits(64)
        self.zobrist_side = {'red': random.getrandbits(64), 'black': random.getrandbits(64)}


    def compute_zobrist_hash(self, board, color):
        h = 0
        for row in range(10):
            for col in range(9):
                piece = board[row][col]
                if piece:
                    h ^= self.zobrist_table[(row, col, piece)]
        h ^= self.zobrist_side[color]
        return h

    def calculate_attack_distance(self, validator, piece, start_pos, king_pos):
        """
        Calculate the minimum number of moves for a piece to reach a position where it can capture the king.
        Returns distance if <= 2, else 3.
        """
        # Check if the piece can attack the king from its current position
        original_piece = validator.board[start_pos[0]][start_pos[1]]
        validator.board[start_pos[0]][start_pos[1]] = piece
        if validator.is_valid_move(start_pos, king_pos):
            validator.board[start_pos[0]][start_pos[1]] = original_piece
            return 0
        validator.board[start_pos[0]][start_pos[1]] = original_piece

        # BFS setup
        queue = [(start_pos, 0)]  # (position, distance)
        visited = {start_pos}
        
        while queue:
            current_pos, dist = queue.pop(0)
            if dist >= 2:  # Limit to 2 moves
                continue
                
            # Explore all possible moves from current_pos
            for to_row in range(10):
                for to_col in range(9):
                    to_pos = (to_row, to_col)
                    # Temporarily place piece at current_pos to check valid moves
                    original_at_current = validator.board[current_pos[0]][current_pos[1]]
                    validator.board[current_pos[0]][current_pos[1]] = piece
                    if validator.is_valid_move(current_pos, to_pos):
                        validator.board[current_pos[0]][current_pos[1]] = original_at_current
                        if to_pos not in visited:
                            visited.add(to_pos)
                            # Check if from to_pos, the piece can attack the king
                            original_at_to = validator.board[to_pos[0]][to_pos[1]]
                            validator.board[to_pos[0]][to_pos[1]] = piece
                            if validator.is_valid_move(to_pos, king_pos):
                                validator.board[to_pos[0]][to_pos[1]] = original_at_to
                                return dist + 1
                            validator.board[to_pos[0]][to_pos[1]] = original_at_to
                            queue.append((to_pos, dist + 1))
                    else:
                        validator.board[current_pos[0]][current_pos[1]] = original_at_current
        return 3  # Distance > 2

    def select_node(self):
        """Select a node to expand using UCT"""
        node = self.root
        while node.untried_moves == [] and node.children:
            node = max(node.children, key=lambda n: n.uct_value(self.exploration_constant))
        return node

    def expand_node(self, node):
        """Expand the node by adding a child with a promising move."""
        if not node.untried_moves:
            return node
        if node.color == self.root.color:  # AI's turn
            # Find opponent's king position in current node's state
            original_board = self.validator.board
            self.validator.board = node.state
            opponent_king_idx = 1 if node.color == 'red' else 0
            opponent_king_pos = self.validator.find_kings()[opponent_king_idx]
            self.validator.board = original_board
            if opponent_king_pos:
                # Choose move that minimizes distance to opponent's king
                best_move = min(
                    node.untried_moves,
                    key=lambda m: abs(m[1][0] - opponent_king_pos[0]) + abs(m[1][1] - opponent_king_pos[1])
                )
            else:
                best_move = random.choice(node.untried_moves)
        else:
            # For opponent's turn, select randomly
            best_move = random.choice(node.untried_moves)
        node.untried_moves.remove(best_move)
        # Create new state by applying the move
        new_state = copy.deepcopy(node.state)
        from_pos, to_pos = best_move
        new_state[to_pos[0]][to_pos[1]] = new_state[from_pos[0]][from_pos[1]]
        new_state[from_pos[0]][from_pos[1]] = None
        # Child node has opponent's color
        child_color = 'red' if node.color == 'black' else 'black'
        child = MCTSNode(new_state, parent=node, move=best_move, color=child_color, flipped=node.validator.flipped)
        node.children.append(child)
        return child

    def simulate(self, node):
        """Enhanced simulation with better strategic play"""
        state = copy.deepcopy(node.state)
        color = node.color
        moves_count = 0
        max_moves = 50
        
        validator = ChessValidator(state, node.validator.flipped)
        while moves_count < max_moves:
            moves = []
            best_move_score = float('-inf')
            best_moves = []
            
            # Get all valid moves and score them
            for row in range(10):
                for col in range(9):
                    piece = state[row][col]
                    if piece and piece[0] == color[0].upper():
                        for to_row in range(10):
                            for to_col in range(9):
                                if validator.is_valid_move((row, col), (to_row, to_col)):
                                    test_state = copy.deepcopy(state)
                                    test_state[to_row][to_col] = test_state[row][col]
                                    test_state[row][col] = None
                                    validator.board = test_state
                                    
                                    if not validator.is_in_check(color):
                                        move_score = 0
                                        # Prioritize checks and captures
                                        if validator.is_in_check('red' if color == 'black' else 'black'):
                                            move_score += 100
                                        if state[to_row][to_col]:  # Capture
                                            move_score += 50
                                        
                                        moves.append(((row, col), (to_row, to_col)))
                                        if move_score > best_move_score:
                                            best_move_score = move_score
                                            best_moves = [((row, col), (to_row, to_col))]
                                        elif move_score == best_move_score:
                                            best_moves.append(((row, col), (to_row, to_col)))
                                    
                                    validator.board = state
            
            if not moves:
                return color != self.root.color
            
            # Choose from best moves with higher probability
            if best_moves and random.random() < 0.8:
                from_pos, to_pos = random.choice(best_moves)
            else:
                from_pos, to_pos = random.choice(moves)
            
            state[to_pos[0]][to_pos[1]] = state[from_pos[0]][from_pos[1]]
            state[from_pos[0]][from_pos[1]] = None
            validator.board = state
            
            if validator.is_checkmate(color):
                return color == self.root.color
            
            color = 'red' if color == 'black' else 'black'
            moves_count += 1
        
        score = self._evaluate_position(state, self.root.color)
        if score > 1000:  # Clear winning position
            return 1.0
        elif score < -1000:  # Clear losing position
            return 0.0
        else:  # Convert score to probability between 0 and 1
            return (score + 5000) / 10000.0

    def backpropagate(self, node, result):
        """Backpropagate the result through the tree"""
        while node:
            node.visits += 1
            node.wins += result
            node = node.parent


    def find_mate_in_n(self, board, color, n, start_time, time_limit):
        if time.time() - start_time > time_limit:
            raise TimeoutError("Checkmate search timeout")
        
        # Check transposition table
        h = self.compute_zobrist_hash(board, color)
        key = (h, n)
        if key in self.mate_transposition_table:
            return self.mate_transposition_table[key]
        
        opponent_color = 'red' if color == 'black' else 'black'
        if n < 1:
            return None
        
        temp_node = MCTSNode(board, color=color, flipped=self.root.validator.flipped)
        moves = temp_node._get_valid_moves(color)
        
        # Prioritize AI moves (existing logic)
        checking_moves = []
        capturing_moves = []
        other_moves = []
        for move in moves:
            if time.time() - start_time > time_limit:
                raise TimeoutError("Checkmate search timeout")
            from_pos, to_pos = move
            new_board = copy.deepcopy(board)
            piece = new_board[from_pos[0]][from_pos[1]]
            new_board[to_pos[0]][to_pos[1]] = piece
            new_board[from_pos[0]][from_pos[1]] = None
            self.validator.board = new_board

            if self.validator.is_checkmate(opponent_color):
            
                return [move]

            if self.validator.is_in_check(opponent_color):
                checking_moves.append(move)

            elif board[to_pos[0]][to_pos[1]]:
                capturing_moves.append(move)
            else:
                other_moves.append(move)
        
        priority_moves = checking_moves + capturing_moves + other_moves
        
        if n == 1:
            self.mate_transposition_table[key] = None
            return None
        
        for move in priority_moves:
            if time.time() - start_time > time_limit:
                raise TimeoutError("Checkmate search timeout")
            
            new_board = copy.deepcopy(board)
            from_pos, to_pos = move
            new_board[to_pos[0]][to_pos[1]] = new_board[from_pos[0]][from_pos[1]]
            new_board[from_pos[0]][from_pos[1]] = None
            
            # Create opponent node and check if in check
            opp_temp_node = MCTSNode(new_board, color=opponent_color, flipped=self.root.validator.flipped)
            self.validator.board = new_board
            in_check = self.validator.is_in_check(opponent_color)
            
            # Get prioritized opponent moves
            opponent_moves = self._get_prioritized_opponent_moves(opp_temp_node, opponent_color, in_check)
            
            all_lead_to_mate = True
            for opp_move in opponent_moves:
                if time.time() - start_time > time_limit:
                    raise TimeoutError("Checkmate search timeout")
                
                opp_board = copy.deepcopy(new_board)
                opp_from, opp_to = opp_move
                opp_board[opp_to[0]][opp_to[1]] = opp_board[opp_from[0]][opp_from[1]]
                opp_board[opp_from[0]][opp_from[1]] = None
                
                mate_sequence = self.find_mate_in_n(opp_board, color, n - 1, start_time, time_limit)
                if mate_sequence is None:
                    all_lead_to_mate = False
                    break
            
            if all_lead_to_mate and opponent_moves:

                result = [move] + mate_sequence
                self.mate_transposition_table[key] = result
                return result
        
        self.mate_transposition_table[key] = None
        return None

    def _get_prioritized_opponent_moves(self, node, opponent_color, in_check):
        """
        Generate a prioritized list of opponent moves.
        If in check, prioritize moves that escape check.
        Otherwise, prioritize capturing and defensive moves.
        """
        all_moves = node._get_valid_moves(opponent_color)
        
        if in_check:
            # Prioritize moves that escape check
            escaping_moves = []
            for move in all_moves:
                from_pos, to_pos = move
                piece = node.state[from_pos[0]][from_pos[1]]
                # Simulate the move
                test_board = copy.deepcopy(node.state)
                test_board[to_pos[0]][to_pos[1]] = piece
                test_board[from_pos[0]][from_pos[1]] = None
                self.validator.board = test_board
                if not self.validator.is_in_check(opponent_color):
                    escaping_moves.append(move)
            # Return escaping moves first, followed by others (though typically only escaping moves are legal)
            return escaping_moves + [m for m in all_moves if m not in escaping_moves]
        else:
            # Prioritize capturing moves, then others
            capturing_moves = []
            other_moves = []
            for move in all_moves:
                from_pos, to_pos = move
                if node.state[to_pos[0]][to_pos[1]]:  # Capture
                    capturing_moves.append(move)
                else:
                    other_moves.append(move)
            return capturing_moves + other_moves

    def pieces_near_king(self, board, ai_color, validator):
        """
        Count AI pieces that can threaten the opponent's king within 2 moves, up to 3 pieces.
        """
        # Find opponent's king position
        opponent_king_pos = validator.find_kings()[1 if ai_color == 'red' else 0]
        if not opponent_king_pos:
            return 0
        
        count = 0
        # Scan the board for AI pieces
        for row in range(10):
            for col in range(9):
                piece = board[row][col]
                if piece and piece[0] == ai_color[0].upper():
                    distance = self.calculate_attack_distance(validator, piece, (row, col), opponent_king_pos)
                    if distance <= 3:
                        count += 1
                        if count >= 3:  # Stop at 3 as per requirement
                            return count
        return count

    def get_best_move(self):
        """Select the best move, prioritizing checkmate sequences."""
        TOTAL_TIME_LIMIT = 180  # Total time limit of 30 seconds
        CHECK_ESCAPE_TIME_LIMIT = 20  # Maximum time for finding best escape from check
        CHECKMATE_TIME_LIMIT = 80  # Maximum time for checkmate search
        
        overall_start_time = time.time()
        
        self.mate_transposition_table.clear()
        
        # When in check, find best escape move with time limit
        if self.validator.is_in_check(self.root.color):

            check_escape_start = time.time()

            moves = []
            try:
                for row in range(10):
                    for col in range(9):
                        # Check time limit for check escape search
                        if time.time() - check_escape_start > CHECK_ESCAPE_TIME_LIMIT:
                            raise TimeoutError("Check escape search timeout")
                            
                        piece = self.root.state[row][col]
                        if piece and piece[0] == self.root.color[0].upper():
                            for to_row in range(10):
                                for to_col in range(9):
                                    if self.validator.is_valid_move((row, col), (to_row, to_col)):
                                        # Try the move
                                        original_piece = self.root.state[to_row][to_col]
                                        self.root.state[to_row][to_col] = piece
                                        self.root.state[row][col] = None
                                        
                                        # Check if move escapes check
                                        if not self.validator.is_in_check(self.root.color):
                                            # Score the move using _evaluate_position
                                            position_score = self._evaluate_position(self.root.state, self.root.color)
                                            moves.append(((row, col), (to_row, to_col), position_score))
                                        
                                        # Undo the move
                                        self.root.state[row][col] = piece
                                        self.root.state[to_row][to_col] = original_piece

                # If there are legal moves to escape check
                if moves:
                    # Sort moves by score, prioritizing moves that lead to better positions
                    moves.sort(key=lambda x: x[2], reverse=True)
                    # Return the highest scored move
                    return (moves[0][0], (moves[0][1]))
            except TimeoutError:
                # If we timeout but have found some moves, use the best one found so far
                if moves:
                    moves.sort(key=lambda x: x[2], reverse=True)
                    return (moves[0][0], (moves[0][1]))
                # If no moves found within time limit, proceed to MCTS search
        
        # if at least a major piece of current player present, return True, otherwise, return False
        # Check for major pieces
        is_major_piece = False
        for r in range(10):
            for c in range(9):
                piece = self.root.state[r][c]
                if piece and piece[0] == self.root.color[0].upper():
                    piece_type = piece[1]
                    # For Chinese chess, all pieces except advisors and elephants can cross river
                    if piece_type in ['車', '馬', '炮', '兵', '卒']:
                        is_major_piece = True
                        break

        if is_major_piece == True:

            checkmate_search_start = time.time()
            
            try:
                # Check for mate in 1 - explicitly pass start time
                mate_in_one = self.find_mate_in_n(self.root.state, self.root.color, 1, checkmate_search_start, CHECKMATE_TIME_LIMIT)
                if mate_in_one:
                    return mate_in_one[0]

                # Check for mate in n if pieces are near opponent's king
                if self.pieces_near_king(self.root.state, self.root.color, self.validator):
                    print()
                    for n in range(2, self.max_mate_depth + 1):
                        print(f'Checking for mate in {n}')
                        # Check both local and overall time limits
                        current_time = time.time()
                        if (current_time - checkmate_search_start > CHECKMATE_TIME_LIMIT or 
                            current_time - overall_start_time > TOTAL_TIME_LIMIT):
                            raise TimeoutError("Time limit exceeded")
                            
                        mate_in_n = self.find_mate_in_n(self.root.state, self.root.color, n, 
                                                       checkmate_search_start, CHECKMATE_TIME_LIMIT)
                        if mate_in_n:
                            self.forced_sequence = mate_in_n[1:]
                            return mate_in_n[0]
                            
            except TimeoutError:
                pass  # Proceed to MCTS search with remaining time
            
        # Calculate remaining time for MCTS search, accounting for both checkmate and check escape time
        time_used = time.time() - overall_start_time
        remaining_time = TOTAL_TIME_LIMIT - time_used
        print(f'time used: {time_used}')
        print(f'remaining time: {remaining_time}')
        
        if remaining_time <= 0:
            # If no time left, make a quick decision based on current best child
            if self.root.children:
                return max(self.root.children, key=lambda n: n.visits).move
            return None

        # Adjust MCTS search time limit to remaining time
        mcts_start_time = time.time()
        while time.time() - mcts_start_time < remaining_time:
            node = self.select_node()
            node = self.expand_node(node)
            result = self.simulate(node)
            self.backpropagate(node, result)

        if not self.root.children:
            return None
        return max(self.root.children, key=lambda n: n.visits).move

    def _evaluate_position(self, state, ai_color):
        """
        Sophisticated position evaluation function for Xiangqi.
        Evaluates material, piece positions (PST), mobility, king safety, and structure.
        Returns score from the perspective of ai_color (positive is good for ai_color).
        """
        total_score = 0
        opponent_color = 'black' if ai_color == 'red' else 'red'
        board_flipped = self.root.validator.flipped # Use flipped status from the root node

        # Use a temporary validator for this specific state evaluation
        validator = ChessValidator(state, board_flipped)

        # --- Pre-computation ---
        game_phase = _determine_game_phase(state)
        red_king_pos, black_king_pos = validator.find_kings()
        king_pos = {'red': red_king_pos, 'black': black_king_pos}

        # --- Initialize Score Components ---
        material_score = 0
        pst_score = 0
        mobility_score = 0
        king_safety_score = 0
        structure_score = 0

        # --- Iterate through board ---
        for r in range(10):
            for c in range(9):
                piece = state[r][c]
                if piece:
                    piece_color_char = piece[0] # 'R' or 'B'
                    piece_type = piece[1]       # '車', '馬', etc.
                    piece_val = PIECE_VALUES[piece_type]
                    current_piece_color = 'red' if piece_color_char == 'R' else 'black'

                    # 1. Material Score
                    base_material = piece_val
                    # Pawn bonus for crossing river (value depends on phase)
                    pawn_bonus = PAWN_ACROSS_RIVER_BONUS_MG + (PAWN_ACROSS_RIVER_BONUS_EG - PAWN_ACROSS_RIVER_BONUS_MG) * game_phase
                    river_crossed = False
                    if piece_type in ['兵', '卒']:
                        if piece_color_char == 'R':
                             river_crossed = (r < 5) if not board_flipped else (r > 4)
                        else: # Black pawn
                             river_crossed = (r > 4) if not board_flipped else (r < 5)
                        if river_crossed:
                            base_material += pawn_bonus

                    if current_piece_color == ai_color:
                        material_score += base_material
                    else:
                        material_score -= base_material

                    # 2. Piece-Square Table Score
                    pst_val = get_pst_score(piece_type, current_piece_color, r, c, board_flipped)
                    if current_piece_color == ai_color:
                        pst_score += pst_val
                    else:
                        pst_score -= pst_val

                    # 3. Mobility Score (Calculated per piece)
                    # Note: This is the most expensive part.
                    piece_mobility = _get_piece_mobility(validator, state, (r, c), current_piece_color)
                    # Simple mobility: count moves
                    # Could add weighting here (e.g., bonus for moves attacking valuable pieces)
                    if current_piece_color == ai_color:
                        mobility_score += piece_mobility
                    else:
                        mobility_score -= piece_mobility


        # 4. King Safety Score (Calculated per king)
        ai_king_safety = _evaluate_king_safety(validator, state, king_pos[ai_color], ai_color, board_flipped)
        opponent_king_safety = _evaluate_king_safety(validator, state, king_pos[opponent_color], opponent_color, board_flipped)
        king_safety_score = ai_king_safety - opponent_king_safety # Positive means AI king safer

        # 5. Structure Score
        red_struct, black_struct = _evaluate_structure(state, board_flipped)
        if ai_color == 'red':
            structure_score = red_struct - black_struct
        else:
            structure_score = black_struct - red_struct


        # --- Combine Scores with Weights ---
        total_score = (
            material_score * MATERIAL_WEIGHT +
            pst_score * PST_WEIGHT +
            mobility_score * MOBILITY_WEIGHT +
            king_safety_score * KING_SAFETY_WEIGHT +
            structure_score * CONNECTED_DEFENDERS_WEIGHT # Example using this weight
        )

        # --- Check/Checkmate Overrides (Crucial) ---
        # Use the temporary validator
        if validator.is_in_check(opponent_color):
            if validator.is_checkmate(opponent_color):
                return 50000  # AI wins (adjust value as needed, must be > max material diff)
            total_score += 200 # Bonus for check (tunable)

        if validator.is_in_check(ai_color):
            # Checkmate check for AI is usually handled by move generation,
            # but double check just in case state is invalid or we missed something
            if validator.is_checkmate(ai_color):
                 return -50000 # AI loses
            total_score -= 200 # Penalty for being in check (tunable)

        return int(total_score) # Return integer score


class ChineseChess:

    def __init__(self):
          
          
        # Add these near the beginning of __init__, after self.window = tk.Tk()
        self.timer_running = False
        self.timer_value = 0
        self.timer_after_id = None
        
           
        self.piece_setting_mode = False
        self.piece_to_place = None
        self.pieces_frame = None
        self.source_canvas = None  # Track which canvas the selected piece is from
        self.records_hidden_by_piece_set = False     
        self.board_copy = [[None for _ in range(9)] for _ in range(10)]  # Initialize empty board copy
        self.copy_switch_board = [[None for _ in range(9)] for _ in range(10)]  # Initialize empty board copy
        
        self.small_highlight_piece_radius = 12
        self.highlight_radius = None
        self.decrease_size = False
        
        self.piece_original_positions = {}  # To track original positions of pieces from side panel
        self.side_panel_pieces = {}  # To track which pieces came from side panel
        
        self.original_piece_info = None
        self.board_piece_info = None
        
        self.start_replay_numbers = []
        
        self.rotate_move_history = []
        self.rotate_move_history_numbers = []
        
        self.check_rotate = False
        self.move_history_numbers = []
        self.history_top_numbers = []
        self.history_bottom_numbers = []

        self.rotate_board = [[None for _ in range(9)] for _ in range(10)]
        self.rotate_single_highlight = []

        self.move_rotate = False

        self.rotate_replay_board = []
        
        self.board_copy_restart = [[None for _ in range(9)] for _ in range(10)]  # Initialize empty board copy        
        self.restart_state = False
        self.set_pieces_mode = False
        self.new_game_state = False
        
        # Replace the available_pieces dictionary with a list of individual pieces
        self.available_pieces = {
            'red': [],
            'black': []
        }
        
        # Define the initial piece layout
        red_piece_layout = [
            ('R帥', 0, 0), ('R仕', 0, 1), ('R仕', 0, 2), ('R相', 0, 3), ('R相', 0, 4),
            ('R馬', 1, 0), ('R馬', 1, 1), ('R車', 1, 2), ('R車', 1, 3), ('R炮', 1, 4), ('R炮', 1, 5),
            ('R兵', 2, 0), ('R兵', 2, 1), ('R兵', 2, 2), ('R兵', 2, 3), ('R兵', 2, 4)
        ]
        
        black_piece_layout = [
            ('B將', 0, 0), ('B士', 0, 1), ('B士', 0, 2), ('B象', 0, 3), ('B象', 0, 4),
            ('B馬', 1, 0), ('B馬', 1, 1), ('B車', 1, 2), ('B車', 1, 3), ('B炮', 1, 4), ('B炮', 1, 5),
            ('B卒', 2, 0), ('B卒', 2, 1), ('B卒', 2, 2), ('B卒', 2, 3), ('B卒', 2, 4)
        ]
        
        # Initialize the available pieces lists
        for piece, row, col in red_piece_layout:
            self.available_pieces['red'].append({
                'piece': piece,
                'row': row,
                'col': col,
                'canvas_id': None,  # Will be set when piece is drawn
                'instance_id': f"{piece}_{row}_{col}"
            })
        
        for piece, row, col in black_piece_layout:
            self.available_pieces['black'].append({
                'piece': piece,
                'row': row,
                'col': col,
                'canvas_id': None,  # Will be set when piece is drawn
                'instance_id': f"{piece}_{row}_{col}"
            })
     
        # Add these new variables for replay functionality
        self.move_history = []  # List to store moves for current game
        self.move_history_records = []
        self.records_seen = False
        
        self.replay_mode = False
        self.current_replay_index = 0
        self.saved_board_states = []  # To store board states for replay
        self.game_over = False  # Add this line
        self.flipped = False  # False means red at bottom, True means black at bottom
                
        self.sound_effect_on = True
        
        pygame.mixer.init()

        # Get absolute path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sound_path = os.path.join(current_dir, "piece_sound5.wav")

        try:
            if os.path.exists(sound_path):
                self.move_sound = pygame.mixer.Sound(sound_path)
                print(f"Sound loaded successfully from: {sound_path}")
            else:
                print(f"Sound file not found at: {sound_path}")
                print(f"Current directory: {current_dir}")
                print(f"Files in directory: {os.listdir(current_dir)}")
                self.move_sound = None
        except Exception as e:
            print(f"Error loading sound: {str(e)}")
            self.move_sound = None

        self.window = tk.Tk()
        
        # And add this code at the beginning of __init__, after self.window = tk.Tk():
        style = ttk.Style()
        style.configure('Custom.TButton', font=('SimSun', 12))
        
        self.window.title("Chinese Chess 7.1.18 (latest version, strong, but takes too much time)")
           
        self.game_history = []  # List to store all games

        # Board dimensions and styling
        self.board_size = 9  # 9x10 board
        self.cell_size = 54
        self.piece_radius = 23  # Smaller pieces to fit on intersections
        self.board_margin = 60  # Margin around the board
        # Calculate total canvas size including margins
        self.canvas_width = self.cell_size * 8 + 2 * self.board_margin
        self.canvas_height = self.cell_size * 9 + 2 * self.board_margin
        
        # Create main horizontal frame to hold board and button side by side
        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack(pady=20, padx=10)
        
        # Create the records frame but don't pack it yet
        self.records_frame = tk.Frame(self.main_frame, height=150)
        
        # Create history menu at the top
        self.create_history_menu()

        # Create move history display
        self.move_text = tk.Text(
            self.records_frame,
            font=("SimSun", 12),
            spacing1=3, spacing3=3,
            width=20,
            height=25,
            state='disabled',
            cursor="arrow"  # Add this line to keep cursor as arrow

        )
        self.move_text.pack(pady=5, padx=(0, 0))
                
        # Create left frame for the board
        self.board_frame = tk.Frame(self.main_frame)
        self.board_frame.pack(side=tk.LEFT, padx=10)
        
        # Create canvas for the game board
        self.canvas = tk.Canvas(
            self.board_frame, 
            width=self.canvas_width,
            height=self.canvas_height,
            bg='#f0d5b0'
        )
        self.canvas.pack()

        # Rest of the initialization code...

        # Create right frame for the button with padding
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(side=tk.LEFT, padx=10, pady=(0, 100))  # Add padding between board and button


        # Create timer label with fixed width font
        self.timer_label = ttk.Label(
            self.button_frame,
            text="000",
            font=('Consolas', 14),
            width=5,
            style='Custom.TButton'
        )
        self.timer_label.pack(pady=(0, 60), side=tk.TOP)


        self.records_button = ttk.Button(
            self.button_frame,
            text="隐藏棋谱" if self.records_seen == True else "打开棋谱",
            command=self.toggle_records,
            width=8,
            style='Custom.TButton'
        )
        self.records_button.pack(pady=5)

        # Create switch color button
        self.switch_color_button = ttk.Button(
            self.button_frame,
            text="红黑对调",
            command=self.switch_colors,
            width=8,
            style='Custom.TButton'
        )
        self.switch_color_button.pack(pady=5)

        self.turn_off_sound_effect = ttk.Button(
            self.button_frame,
            
            text="关闭音效" if self.sound_effect_on == True else "打开音效",
            command=self.sound_effect,
            width=8,
            style='Custom.TButton'
        )
        self.turn_off_sound_effect.pack(pady=5, before=self.records_button)

        self.new_game_button = ttk.Button(
            self.button_frame,
            text="新对局",
            command=self.start_new_game,
            width=8,
            style='Custom.TButton'
        )
        self.new_game_button.pack(pady=5, before=self.turn_off_sound_effect)

        # Create restart button
        self.restart_button = ttk.Button(
            self.button_frame,
            text="再来一盘",  # Keep the original Chinese text
            command=self.restart_game,
            width=8,
            style='Custom.TButton'
        )
        self.restart_button.pack(pady=5)
        
        # Create replay button
        self.replay_button = ttk.Button(
            self.button_frame,
            text="复盘",
            command=self.start_replay,
            width=8,
            style='Custom.TButton'
        )
        self.replay_button.pack(pady=5)

        # Create previous move button (initially disabled)
        self.prev_move_button = ttk.Button(
            self.button_frame,
            text="上一步",
            command=self.prev_replay_move,
            width=8,
            style='Custom.TButton',
            state=tk.DISABLED
        )
        self.prev_move_button.pack(pady=5)
                                
        # Create next move button (initially disabled)
        self.next_move_button = ttk.Button(
            self.button_frame,
            text="下一步",
            command=self.next_replay_move,
            width=8,
            style='Custom.TButton',
            state=tk.DISABLED
        )
        self.next_move_button.pack(pady=5)
        
        # Create set pieces button
        self.set_pieces_button = ttk.Button(
            self.button_frame,
            text="摆放棋子",
            command=self.toggle_piece_setting_mode,
            width=8,
            style='Custom.TButton'
        )
        self.set_pieces_button.pack(pady=5, before=self.new_game_button)

        self.set_button_states_for_gameplay()

        # Initialize game state
        self.selected_piece = None
        self.highlighted_positions = []
        self.current_player = 'red'  # Red moves first
        self.initialize_board()
        
        # Draw column numbers at top and bottom
        # List of Chinese numbers for red side
        self.red_numbers = ['九', '八', '七', '六', '五', '四', '三', '二', '一']
        self.red_numbers_flipped = ['一', '二', '三', '四', '五', '六', '七', '八', '九']    

        # List of Arabic numbers for black side
        self.black_numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
        self.black_numbers_flipped = ['9', '8', '7', '6', '5', '4', '3', '2', '1']   
        
        self.top_numbers = self.black_numbers
        self.bottom_numbers = self.red_numbers
        
        self.draw_board()
                    
        # Bind mouse event
        self.canvas.bind('<Button-1>', self.on_click)

    def enable_history_menu(self):
        """Enable the history menu"""
        if hasattr(self, 'history_menu'):
            self.history_menu.config(state='readonly')

    def disable_history_menu(self):
        """Disable the history menu"""
        if hasattr(self, 'history_menu'):
            self.history_menu.config(state='disabled')

    def create_history_menu(self):
        """Create a menu for opening game histories"""
        # Create a frame for the menu at the top of records frame
        self.history_menu_frame = tk.Frame(self.records_frame)
        self.history_menu_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        # Create a dropdown menu
        self.history_var = tk.StringVar()
        self.history_var.set("历史对局")  # Default text
        
        # Create and pack the dropdown menu
        self.history_menu = ttk.Combobox(
            self.history_menu_frame, 
            textvariable=self.history_var,
            state='readonly',
            width=17,
            font=("SimSun", 12)
        )
        self.history_menu.pack(side=tk.LEFT, padx=2)
        
        # Bind the selection event
        self.history_menu.bind('<<ComboboxSelected>>', self.load_selected_game)
        
        # Initial population of the history list
        self.refresh_history_list()


    def refresh_history_list(self):
        """Refresh the list of available game history files"""
        import os
        from datetime import datetime

        # Configure style for the Combobox popup
        style = ttk.Style()
        style.configure('TCombobox', font=('SimSun', 12))
        style.configure('Combobox.Listbox', font=('SimSun', 12))  # Configure popup list font

        # Configure Combobox
        self.history_menu.configure(font=('SimSun', 12))
        self.history_menu.option_add('*TCombobox*Listbox.font', ('SimSun', 12))  # Set popup list font

        # Get list of TXT files from game_records directory
        records_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chinese_chess_records")
        if not os.path.exists(records_dir):
            os.makedirs(records_dir)
        
        pgn_files = []
        for file in os.listdir(records_dir):
            if file.endswith(".txt"):
                try:
                    file_path = os.path.join(records_dir, file)
                    mod_time = os.path.getmtime(file_path)
                    try:
                        date_str = file.split('game_')[1].split('.')[0]
                        file_time = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                    except:
                        file_time = datetime.fromtimestamp(mod_time)
                    pgn_files.append((file_time, file))
                except:
                    pgn_files.append((datetime.now(), file))
        
        # Sort files by time, newest first
        pgn_files.sort(reverse=True)
        
        # Format display strings for the dropdown
        display_list = []
        self.pgn_file_map = {}  # Map display strings to filenames
        
        for creation_time, filename in pgn_files:
            # For external files without timestamp in name, use a different format
            if filename.startswith('game_'):
                # Use smaller font for auto-saved games
                display_text = f"{creation_time.strftime('%m-%d %H:%M')} 对局"
            else:
                # Use original name for external files
                display_text = filename.replace('.txt', '')
            display_list.append(display_text)
            self.pgn_file_map[display_text] = filename
        
        # Configure font for the dropdown menu
        self.history_menu.configure(font=("SimSun", 12))
        
        # Update the dropdown menu
        self.history_menu['values'] = display_list
        if display_list:
            self.history_menu.set("历史对局")

        # Configure dropdown style
        style = ttk.Style()
        self.history_menu.configure(style='TCombobox')


    def load_selected_game(self, event=None):
        """Load and display the selected game history"""
        selected = self.history_var.get()
        if selected == "历史对局" or selected not in self.pgn_file_map:
            return
        
        filename = self.pgn_file_map[selected]
        records_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chinese_chess_records")
        file_path = os.path.join(records_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Initialize board to starting position
            self.initialize_board()  # Set up initial board
            self.board_copy = [row[:] for row in self.board]  # Store initial state
            current_board = [row[:] for row in self.board]  # Working copy
            self.move_history = []
            self.move_history_records = []
            self.move_history_numbers = []
            self.highlighted_positions = []
            self.current_player = 'red'
            
            # Draw initial board immediately
            self.draw_board()
            
            # Split moves and filter out empty strings and 'END'
            moves = [move.strip() for move in content.split() if move.strip() and move != "END"]
            
            # Process each move and translate to Chinese notation
            for move in moves:
                try:
                    coords = move.split('-')
                    if len(coords) != 2:
                        continue
                        
                    from_coord, to_coord = coords
                    from_col = ord(from_coord[0]) - ord('A')
                    from_row = 9 - int(from_coord[1])
                    to_col = ord(to_coord[0]) - ord('A')
                    to_row = 9 - int(to_coord[1])
                    
                    piece = current_board[from_row][from_col]
                    if piece:
                        chinese_notation = self.get_move_text(
                            (from_row, from_col),
                            (to_row, to_col),
                            piece,
                            current_board
                        )
                        
                        current_board[to_row][to_col] = piece
                        current_board[from_row][from_col] = None
                        
                        self.move_history.append({
                            'from_pos': (from_row, from_col),
                            'to_pos': (to_row, to_col),
                            'piece': piece,
                            'board_state': [row[:] for row in current_board]
                        })
                        self.move_history_records.append(chinese_notation)
                        self.move_history_numbers.append([self.top_numbers, self.bottom_numbers])
                        
                except (IndexError, ValueError) as e:
                    print(f"Error processing move: {move}, {str(e)}")
                    continue
           
            # Update the display with Chinese notation
            self.move_text.config(state='normal')
            self.move_text.delete('1.0', tk.END)
            
            # Display moves in pairs with Chinese notation
            move_count = len(self.move_history_records)
            for i in range(0, move_count, 2):
                move_number = (i // 2) + 1
                red_move = self.move_history_records[i]
                if i + 1 < move_count:
                    black_move = self.move_history_records[i + 1]
                    self.move_text.insert(tk.END, f"{move_number}. {red_move}\n")
                    take_up_space = ' ' * len(str(move_number))
                    self.move_text.insert(tk.END, f"{take_up_space}  {black_move}\n")
                else:
                    self.move_text.insert(tk.END, f"{move_number}. {red_move}\n")
            
            self.move_text.config(state='disabled')
            self.move_text.see('1.0')  # Scroll to the top
            
            # Enable replay functionality
            self.replay_mode = True
            self.current_replay_index = 0
            self.board = [row[:] for row in self.board_copy]
            self.draw_board()
            
            # Set button states for replay
            self.replay_button.config(state=tk.DISABLED)
            self.next_move_button.config(state=tk.NORMAL)
            self.prev_move_button.config(state=tk.DISABLED)
            
            # Show records if they're hidden
            if not self.records_seen:
                self.toggle_records()
                
        except Exception as e:
            self.show_centered_warning("错误", f"无法加载对局记录: {str(e)}")

    def convert_pgn_to_board_position(self, pgn_move, current_board, color):
        """Convert a PGN format move to board positions"""
        # Split the move into piece and coordinates
        piece_char = pgn_move[0]
        coords = pgn_move[1:].split('-')
        if len(coords) != 2:
            return None, None

        from_coord, to_coord = coords
        
        # Convert file letter to column number (A-I -> 0-8)
        from_col = ord(from_coord[0]) - ord('A')
        to_col = ord(to_coord[0]) - ord('A')
        
        # Convert rank number to row number (0-9)
        from_row = 9 - int(from_coord[1])
        to_row = 9 - int(to_coord[1])
        
        # Validate positions
        if not (0 <= from_col <= 8 and 0 <= to_col <= 8 and 0 <= from_row <= 9 and 0 <= to_row <= 9):
            return None, None
        
        return (from_row, from_col), (to_row, to_col)

    def convert_to_pgn_coordinate(self, row, col, flipped=False):
        """Convert board coordinates to PGN format (a-i for columns, 0-9 for rows)"""
        if not flipped:
            pgn_col = chr(ord('A') + col)
            pgn_row = str(9 - row)
        else:
            pgn_col = chr(ord('A') + (8 - col))
            pgn_row = str(row)
        return pgn_col + pgn_row
        
    def save_game_to_pgn(self):
        """Save the game history to a TXT file in coordinate format"""
        if not self.move_history:
            return
                
        import os
        from datetime import datetime
        
        records_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chinese_chess_records")
        if not os.path.exists(records_dir):
            os.makedirs(records_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(records_dir, f"game_{timestamp}.txt")
        
        with open(filename, 'w', encoding='utf-8') as f:
            # Save moves in coordinate format
            for move in self.move_history:
                from_pos = move['from_pos']
                to_pos = move['to_pos']
                
                # Convert positions to coordinates
                from_coord = chr(ord('A') + from_pos[1]) + str(9 - from_pos[0])
                to_coord = chr(ord('A') + to_pos[1]) + str(9 - to_pos[0])
                
                # Write move in format "E5-C6"
                f.write(f"{from_coord}-{to_coord} ")
            
            f.write("END")
        

    def start_timer(self):
        """Start the timer"""
        self.timer_value = 0
        self.timer_running = True
        self.update_timer()

    def stop_timer(self):
        """Stop the timer"""
        self.timer_running = False
        if self.timer_after_id:
            self.window.after_cancel(self.timer_after_id)
            self.timer_after_id = None

    def update_timer(self):
        """Update the timer display"""
        if self.timer_running:
            self.timer_value += 1
            # Format timer value to 3 digits with leading zeros
            self.timer_label.config(text=f"{self.timer_value:03d}")
            self.timer_after_id = self.window.after(1000, self.update_timer)

    def execute_ai_move(self, best_move, ai_color):
        """Execute the AI's move on the main thread"""
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
        
        self.stop_timer()  # Stop timer when AI starts its move

        # Switch players
        self.current_player = 'red' if ai_color == 'black' else 'black'
        
        self.switch_color_button.config(state=tk.NORMAL)
        
        # Handle rotation if needed
        self.move_rotate = False
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
            self.enable_history_menu()

        else:
            self.game_over = False
        
        # Check if the opponent is now in checkmate
        opponent_color = 'black' if ai_color == 'red' else 'red'
        if not self.is_checkmate(opponent_color):
            self.game_over = False

    def on_record_click(self, event):
        """Handle clicks on the move records"""
        if not self.replay_mode:
            return

        # Get the clicked line number
        index = self.move_text.index(f"@{event.x},{event.y}")
        line_number = int(index.split('.')[0]) - 1  # Convert to 0-based index
        
        if 0 <= line_number < len(self.move_history):
            # Update replay index and board state
            self.current_replay_index = line_number + 1
            move = self.move_history[line_number]
            
            # Restore board state
            for i in range(len(self.board)):
                self.board[i] = move['board_state'][i][:]
            
            # Highlight the move
            self.highlighted_positions = [move['from_pos'], move['to_pos']]
            
            if self.move_history_numbers[line_number]:
                self.top_numbers = self.move_history_numbers[line_number][0]
                self.bottom_numbers = self.move_history_numbers[line_number][1]
            
            # Update button states
            self.prev_move_button.config(state=tk.NORMAL)
            self.next_move_button.config(
                state=tk.NORMAL if self.current_replay_index < len(self.move_history) else tk.DISABLED
            )
            
            # Highlight the current move in records
            self.highlight_current_move(line_number)
            
            # Redraw the board
            self.draw_board()

    def rotate_to_replay(self):
        """Switch the board orientation by rotating it 180 degrees"""
       
        # Clear the board
        self.rotate_board = [[None for _ in range(9)] for _ in range(10)]
        # Rotate pieces 180 degrees
        for row in range(10):
            for col in range(9):
                if self.board[row][col]:
                    new_row = 9 - row
                    new_col = 8 - col
                    self.rotate_board[new_row][new_col] = self.board[row][col]
                    
        # Rotate highlighted positions
        self.rotate_single_highlight = []
        for pos in self.highlighted_positions:
            if pos:
                row, col = pos

                new_row = 9 - row
                new_col = 8 - col

                self.rotate_single_highlight.append((new_row, new_col))
        
        # Update selected piece position if any
        rotate_piece = (None, None)
        if self.selected_piece:
            row, col = self.selected_piece
            rotate_piece = (9 - row, 8 - col)
        
    def start_new_game(self):
        
        self.stop_timer()  # Stop timer when AI starts its move
        self.timer_label.config(text='000')
        self.disable_history_menu()

        self.check_rotate = False
        self.rotate_board = [[None for _ in range(9)] for _ in range(10)]
        self.rotate_single_highlight = []
        self.rotate_replay_board = []
        self.move_history_numbers = []

        self.switch_color_button.config(state=tk.NORMAL)
        self.new_game_button.destroy()
        self.new_game_button = ttk.Button(
            self.button_frame,
            text="新对局",
            command=self.start_new_game,
            width=8,
            style='Custom.TButton'
        )
        self.new_game_button.pack(pady=5, before=self.turn_off_sound_effect)

        self.new_game_state = True
            
        # Store the current game's move history if it exists
        if self.move_history:
            self.game_history.append(self.move_history)
        self.move_history = []
        self.move_history_records = []  # Clear the records list
        
        # Reset game state
        self.selected_piece = None
        self.highlighted_positions = []
        self.current_player = 'red'
        self.replay_mode = False
        self.current_replay_index = 0            
        self.game_over = False
                    
        # Set button states for normal gameplay
        self.set_button_states_for_gameplay()
                
        # Clear the records display
        if self.move_text:
            self.move_text.config(state='normal')
            self.move_text.delete('1.0', tk.END)
            self.move_text.config(state='disabled')
        
        # Reinitialize the board
        self.initialize_board()
        self.draw_board()
        self.board_copy_restart = [row[:] for row in self.board]

        # If the board is flipped, set current player to red and trigger immediate AI move
        if self.flipped:
            self.current_player = 'red'  # Set to red so AI plays as red
            self.window.after(100, self.make_ai_move)  # Small delay to ensure board is redrawn first


    def is_valid_piece_position(self, piece, row, col):
        """
        Check if a piece is in a valid position on the board.
        Returns True if the position is valid, False otherwise.
        """
        piece_type = piece[1]
        is_red = piece[0] == 'R'
        
        if piece_type in ['帥', '將']:  # King
            # Kings must be in their palace (3x3 grid)
            if not self.flipped:
                if is_red and not (7 <= row <= 9 and 3 <= col <= 5):
                    return False
                if not is_red and not (0 <= row <= 2 and 3 <= col <= 5):
                    return False
            else:
                if is_red and not (0 <= row <= 2 and 3 <= col <= 5):
                    return False
                if not is_red and not (7 <= row <= 9 and 3 <= col <= 5):
                    return False
        
        elif piece_type in ['仕', '士']:  # Advisor
            # Advisors must be in their palace
            if not self.flipped:
                if is_red and (row, col) not in [(7, 3), (7, 5), (9, 3), (9, 5), (8, 4)]:
                    return False
                if not is_red and (row, col) not in [(0, 3), (0, 5), (2, 3), (2, 5), (1, 4)]:
                    return False
            else:
                if is_red and (row, col) not in [(0, 3), (0, 5), (2, 3), (2, 5), (1, 4)]:
                    return False
                if not is_red and (row, col) not in [(7, 3), (7, 5), (9, 3), (9, 5), (8, 4)]:
                    return False
        
        elif piece_type in ['相', '象']:  # Elephant
            # Elephants cannot cross the river
            if not self.flipped:
                if is_red and (row, col) not in [(5, 2), (5, 6), (7, 0), (7, 4), (7, 8), (9, 2), (9, 6)]:  # Red elephant cannot cross to black's side
                    return False
                if not is_red and (row, col) not in [(0, 2), (0, 6), (2, 0), (2, 4), (2, 8), (4, 2), (4, 6)]:  # Black elephant cannot cross to red's side
                    return False
            else:
                if is_red and (row, col) not in [(0, 2), (0, 6), (2, 0), (2, 4), (2, 8), (4, 2), (4, 6)]:  # Red elephant cannot cross to black's side
                    return False
                if not is_red and (row, col) not in [(5, 2), (5, 6), (7, 0), (7, 4), (7, 8), (9, 2), (9, 6)]:  # Black elephant cannot cross to red's side
                    return False
        
        if piece_type in ['兵', '卒']:

            if not self.flipped:
                if is_red:
                    if (7 <= row <= 9 and 0 <= col <= 8) or (row, col) in [(5, 1), (6, 1), (5, 3), (6, 3), (5, 5), (6, 5), (5, 7), (6, 7)]:
                        return False
                if not is_red:
                    if (0 <= row <= 2 and 0 <= col <= 8) or (row, col) in [(3, 1), (4, 1), (3, 3), (4, 3), (3, 5), (4, 5), (3, 7), (4, 7)]:
                        return False
            else:
                if is_red:
                    if (0 <= row <= 2 and 0 <= col <= 8) or (row, col) in [(3, 1), (4, 1), (3, 3), (4, 3), (3, 5), (4, 5), (3, 7), (4, 7)]:
                        return False
                if not is_red:
                    if (7 <= row <= 9 and 0 <= col <= 8) or (row, col) in [(5, 1), (6, 1), (5, 3), (6, 3), (5, 5), (6, 5), (5, 7), (6, 7)]:
                        return False
        
        return True

    def validate_piece_positions(self):
        """
        Validate all piece positions on the board.
        Returns True if all pieces are in valid positions, False otherwise.
        """

        collect_kings = []
        
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece:
                    if piece[1] in ['帥', '將', '仕', '士', '相', '象', '兵', '卒']:
                        if piece[1] in ['帥', '將']:
                            collect_kings.append(piece[1])
                            
                        if not self.is_valid_piece_position(piece, row, col):
                            return False

        if len(collect_kings) != 2:
            return False                            
                
        if self.is_in_check('black') or self.is_in_check('red'):
            return False
                            
        return True

    def toggle_piece_setting_mode(self):
        """Toggle between normal game mode and piece setting mode"""
        self.piece_setting_mode = not self.piece_setting_mode
        self.restart_state = False
        self.replay_mode = False

        self.replay_button.config(state=tk.DISABLED)

        self.prev_move_button.config(state=tk.DISABLED)
        self.next_move_button.config(state=tk.DISABLED)

        if self.records_seen == True and self.piece_setting_mode == True:
            self.toggle_records()
            self.records_hidden_by_piece_set = True

        if self.piece_setting_mode == False:
            
            # Store the current game's move history if it exists
            if self.move_history:
                self.game_history.append(self.move_history)
            self.move_history = []
            self.move_history_records = []  # Clear the records list
            
        if self.piece_setting_mode == False and self.flipped == False:
            self.current_player = 'red'

        if self.piece_setting_mode:

            self.set_pieces_button.destroy()
            # Create set pieces button
            self.set_pieces_button = ttk.Button(
                self.button_frame,
                text="完成摆放",
                command=self.toggle_piece_setting_mode,
                width=8,
                style='Custom.TButton'
            )
            self.set_pieces_button.pack(pady=5, before=self.new_game_button)

            # Clear the board
            self.board = [[None for _ in range(9)] for _ in range(10)]
            self.highlighted_positions = []
            self.draw_board()

            # Reset available pieces
            self.reset_available_pieces()
            
            # Create/show pieces frame
            if not self.pieces_frame:
                self.create_pieces_frame()
            else:
                # Destroy old frame and create new one to ensure clean state
                self.pieces_frame.destroy()
                self.create_pieces_frame()
            
            # Pack the pieces frame with padding
            self.pieces_frame.pack(side=tk.RIGHT, padx=5)
            
        else:

            self.stop_timer()  # Stop timer when AI starts its move
            self.timer_label.config(text='000')
            self.disable_history_menu()

            if not self.validate_piece_positions():

                # Show warning and revert to piece setting mode
                self.show_centered_warning("Invalid Positions", "棋子摆放不正确 ！")
                self.piece_setting_mode = True
                
                self.set_pieces_button.destroy()
                # Create set pieces button
                self.set_pieces_button = ttk.Button(
                    self.button_frame,
                    text="完成摆放",
                    command=self.toggle_piece_setting_mode,
                    width=8,
                    style='Custom.TButton'
                )
                self.set_pieces_button.pack(pady=5, before=self.new_game_button)
                
                return

            self.set_pieces_button.destroy()
            # Create set pieces button
            self.set_pieces_button = ttk.Button(
                self.button_frame,
                text="摆放棋子",
                command=self.toggle_piece_setting_mode,
                width=8,
                style='Custom.TButton'
            )
            self.set_pieces_button.pack(pady=5, before=self.new_game_button)

            if self.records_hidden_by_piece_set == True:

                self.toggle_records()
                self.records_hidden_by_piece_set = False
            
            # Pack the pieces frame with padding
            self.pieces_frame.pack(side=tk.RIGHT, padx=5)
            
            self.move_history_numbers = []

            self.highlighted_positions = []
            self.draw_board()

            self.switch_color_button.config(state=tk.NORMAL)
            
            if self.flipped:
                self.window.after(500, self.make_ai_move)
                
            # Hide pieces frame
            if self.pieces_frame:
                self.pieces_frame.pack_forget()
            
            # Reset button text
            self.set_pieces_button.config(text="摆放棋子")
            
            self.game_over = False
            
            # Clear selection
            self.piece_to_place = None

    def create_pieces_frame(self):
        self.pieces_frame = tk.Frame(self.main_frame)
        piece_canvas_size = self.cell_size * 6
        
        # Create frames for top and bottom sections
        top_frame = tk.Frame(self.pieces_frame)
        bottom_frame = tk.Frame(self.pieces_frame)
                
        top_frame.pack(side=tk.TOP, pady=10)
        bottom_frame.pack(side=tk.BOTTOM, pady=10)
        
        def create_piece_section(frame, color_prefix):
            canvas = tk.Canvas(
                frame,
                width=piece_canvas_size + 5,
                height=self.cell_size * 3 + 5,
                bg='#f0d5b0'
            )
            canvas.pack(padx=5)

            # Define piece layouts
            piece_layout = []
            if color_prefix == 'R':  # Red pieces
                piece_layout = [
                    [('R帥',1), ('R仕',1), ('R仕',1), ('R相',1), ('R相',1)],
                    [('R兵',1), ('R兵',1), ('R兵',1), ('R兵',1), ('R兵',1)],
                    [('R馬',1), ('R馬',1), ('R車',1), ('R車',1), ('R炮',1), ('R炮',1)]
                ]
            else:  # Black pieces
                piece_layout = [
                    [('B將',1), ('B士',1), ('B士',1), ('B象',1), ('B象',1)],
                    [('B卒',1), ('B卒',1), ('B卒',1), ('B卒',1), ('B卒',1)],
                    [('B馬',1), ('B馬',1), ('B車',1), ('B車',1), ('B炮',1), ('B炮',1)]
                ]

            # Draw pieces based on layout
            for row, pieces_row in enumerate(piece_layout):
                for col, piece_info in enumerate(pieces_row):
                    if piece_info:
                        piece, _ = piece_info
                        x = col * self.cell_size + self.cell_size // 2 + 4
                        y = row * self.cell_size + self.cell_size // 2 + 4
                        
                        instance_id = f"{piece}_{row}_{col}"
                        piece_group = []
                        
                        # Draw piece circle
                        circle = canvas.create_oval(
                            x - self.piece_radius, y - self.piece_radius,
                            x + self.piece_radius, y + self.piece_radius,
                            fill='white',
                            outline='red' if piece.startswith('R') else 'black',
                            width=2,
                            tags=(instance_id,)
                        )
                        piece_group.append(circle)

                        # Draw piece text
                        text = canvas.create_text(
                            x, y,
                            text=piece[1],
                            fill='red' if piece.startswith('R') else 'black',
                            font=('KaiTi', 25, 'bold'),
                            tags=(instance_id,)
                        )
                        piece_group.append(text)

                        for item in piece_group:
                            canvas.tag_bind(instance_id, '<Button-1>', 
                                lambda e, c=canvas, i=instance_id, p=piece: self.select_piece_from_canvas(e, c, i, p))

            return canvas

        # Create red and black piece sections based on flipped state
        if self.flipped:
            # When flipped, red pieces go on top, black pieces on bottom
            self.red_canvas = create_piece_section(top_frame, 'R')
            self.black_canvas = create_piece_section(bottom_frame, 'B')
        else:
            # When not flipped, black pieces go on top, red pieces on bottom
            self.black_canvas = create_piece_section(top_frame, 'B')
            self.red_canvas = create_piece_section(bottom_frame, 'R')

    def select_piece_from_canvas(self, event, canvas, instance_id, piece):
        """Handle piece selection from the pieces canvas"""
        # Clear previous highlights from all canvases
        self.red_canvas.delete('highlight')
        self.black_canvas.delete('highlight')

        self.highlighted_positions = []
        self.draw_board()
        
        # Find the item's coordinates
        items = canvas.find_withtag(instance_id)
        if items:
            circle = items[0]  # The circle is always the first item
            bbox = canvas.bbox(circle)
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            # Store the selected piece info
            self.piece_to_place = piece
            self.source_canvas = canvas
            self.selected_instance_id = instance_id
            
            # Store original position information
            self.piece_original_positions[instance_id] = {
                'x': center_x,
                'y': center_y,
                'piece': piece,
                'canvas': canvas
            }
            
            # Create highlight
            canvas.create_rectangle(
                center_x - self.piece_radius - 2,
                center_y - self.piece_radius - 2,
                center_x + self.piece_radius + 2,
                center_y + self.piece_radius + 2,
                outline='yellow',
                width=2,
                tags='highlight'
            )

    def select_piece_to_place(self, piece):
        """Handle piece selection for placement"""
        self.piece_to_place = piece
        # Clear previous highlights
        self.selected_piece = None
        self.highlighted_positions = []
        self.draw_board()

    def reset_available_pieces(self):
        """Reset the available pieces to their initial counts"""
        self.available_pieces = {
            'red': {
                'R帥': 1, 'R仕': 2, 'R相': 2, 'R馬': 2,
                'R車': 2, 'R炮': 2, 'R兵': 5
            },
            'black': {
                'B將': 1, 'B士': 2, 'B象': 2, 'B馬': 2,
                'B車': 2, 'B炮': 2, 'B卒': 5
            }
        }


    def on_click(self, event):
        
        self.rotate_board = [[None for _ in range(9)] for _ in range(10)]
        self.rotate_single_highlight = []
        
        if len(self.move_history) == 0:
            self.board_copy = [row[:] for row in self.board]


        if self.piece_setting_mode:
            # Convert click coordinates to board position
            col = round((event.x - self.board_margin) / self.cell_size)
            row = round((event.y - self.board_margin) / self.cell_size)
            mouse_x = event.x
            mouse_y = event.y
            
            # Check if click is near side panel
            is_near_panel = (
                mouse_x > self.canvas_width + 20 or  # Right side panel
                mouse_x < 0  # Left side panel
            )
            
            # First check if we clicked within the board bounds
            if 0 <= row < 10 and 0 <= col < 9:
                if self.piece_to_place:  # If we have a piece selected
                    # Place the new piece
                    self.board[row][col] = self.piece_to_place
                    self.highlighted_positions = [(row, col)]
                    
                    # If piece is from side panel, store its board position
                    if self.selected_instance_id:
                        self.side_panel_pieces[(row, col)] = {
                            'instance_id': self.selected_instance_id,
                            'original_info': self.piece_original_positions.get(self.selected_instance_id)
                        }
                    
                    # Remove piece from source canvas if it came from there
                    if self.source_canvas and self.selected_instance_id:
                        items = self.source_canvas.find_withtag(self.selected_instance_id)
                        for item in items:
                            self.source_canvas.delete(item)
                        self.source_canvas.delete('highlight')
                    
                    self.draw_board()
                    
                    # Reset selection states
                    self.piece_to_place = None
                    self.source_canvas = None
                    self.selected_instance_id = None
                else:  # If we're picking up an existing piece from the board
                    piece = self.board[row][col]
                    if piece:
                        self.decrease_size = True
                        self.highlighted_positions = [(row, col)]
                        # Store the piece and clear its position
                        self.piece_to_place = piece
                        # Check if this piece came from side panel
                        if (row, col) in self.side_panel_pieces:
                            self.selected_instance_id = self.side_panel_pieces[(row, col)]['instance_id']
                            original_info = self.side_panel_pieces[(row, col)]['original_info']
                            if original_info:
                                self.source_canvas = original_info['canvas']
                                 
                        self.board[row][col] = None
                        self.draw_board()
            
            # Handle returns to side panel
            elif self.piece_to_place and is_near_panel:
                # If the piece was originally from side panel, restore it
                if self.selected_instance_id and self.selected_instance_id in self.piece_original_positions:
                    original_info = self.piece_original_positions[self.selected_instance_id]
                    canvas = original_info['canvas']
                    x = original_info['x']
                    y = original_info['y']
                    piece = original_info['piece']
                    
                    # Redraw the piece in its original position
                    circle = canvas.create_oval(
                        x - self.piece_radius, y - self.piece_radius,
                        x + self.piece_radius, y + self.piece_radius,
                        fill='white',
                        outline='red' if piece.startswith('R') else 'black',
                        width=2,
                        tags=(self.selected_instance_id,)
                    )
                    
                    text = canvas.create_text(
                        x, y,
                        text=piece[1],
                        fill='red' if piece.startswith('R') else 'black',
                        font=('KaiTi', 25, 'bold'),
                        tags=(self.selected_instance_id,)
                    )
                    
                    # Rebind the click event
                    for item in [circle, text]:
                        canvas.tag_bind(
                            self.selected_instance_id, 
                            '<Button-1>', 
                            lambda e, c=canvas, i=self.selected_instance_id, p=piece: 
                                self.select_piece_from_canvas(e, c, i, p)
                        )
                    
                    # Clean up references
                    for pos, info in list(self.side_panel_pieces.items()):
                        if info['instance_id'] == self.selected_instance_id:
                            del self.side_panel_pieces[pos]
                    
                    # Reset selection states
                    self.piece_to_place = None
                    self.source_canvas = None
                    self.selected_instance_id = None
                    self.draw_board()
                
            return  # Exit the function early to prevent normal game logic


        if (self.flipped == False and self.current_player == 'black') or (self.flipped == True and self.current_player == 'red'):
            return

        if self.replay_mode or self.game_over:  # Add game_over check
            return  # Ignore clicks when game is over or in replay mode
        
        # Convert click coordinates to board position
        col = round((event.x - self.board_margin) / self.cell_size)
        row = round((event.y - self.board_margin) / self.cell_size)
                
        # Ensure click is within board bounds
        if 0 <= row < 10 and 0 <= col < 9:
            clicked_piece = self.board[row][col]
            
            # If a piece is already selected
            if self.selected_piece:
                start_row, start_col = self.selected_piece
                
                # If clicking on another piece of the same color, select that piece instead
                if (clicked_piece and 
                    clicked_piece[0] == self.current_player[0].upper()):
                    self.selected_piece = (row, col)
                    self.highlighted_positions = [(row, col)]  # Reset highlights for new selection
                    self.draw_board()
                # If clicking on a valid move position
                elif self.is_valid_move(self.selected_piece, (row, col)):
                    # Store the current state to check for check
                    original_piece = self.board[row][col]
                    
                    # Make the move temporarily
                    self.board[row][col] = self.board[start_row][start_col]
                    self.board[start_row][start_col] = None
                    
                    # Check if the move puts own king in check
                    if self.is_in_check(self.current_player):
                        # Undo the move if it puts own king in check
                        self.board[start_row][start_col] = self.board[row][col]
                        self.board[row][col] = original_piece

                        if self.current_player == 'red':
                            self.show_centered_warning("Invalid Move", "你正在被将军")
                        else:
                            self.show_centered_warning("Invalid Move", "黑方正在被将军")

                    else:
                        # Keep both the original and new positions highlighted
                        self.highlighted_positions = [(start_row, start_col), (row, col)]

                        # Play move sound
                        if self.sound_effect_on:
                                                        
                            if hasattr(self, 'move_sound') and self.move_sound:
                                self.move_sound.play()
                                
                        self.add_move_to_records(
                            (start_row, start_col),
                            (row, col),
                            self.board[row][col]
                        )

                        # Switch players
                        self.current_player = 'black' if self.current_player == 'red' else 'red'

                        self.window.after(500, self.make_ai_move)

                        self.move_rotate = False
                        if self.check_rotate == True:

                            self.move_rotate = True

                            self.rotate_to_replay()
                            (start_row, start_col) = self.rotate_single_highlight[0]
                            (row, col) = self.rotate_single_highlight[1]

                            self.history_top_numbers = []
                            self.history_bottom_numbers = []

                            self.history_top_numbers[:] = self.bottom_numbers[:]
                            self.history_bottom_numbers[:] = self.top_numbers[:]

                            self.history_top_numbers.reverse()
                            self.history_bottom_numbers.reverse()

                            self.move_history_numbers.append([self.history_top_numbers, self.history_bottom_numbers])
                        else:

                            self.move_history_numbers.append([self.top_numbers, self.bottom_numbers])

                        # Add this line to record the move
                        self.add_move_to_history(
                            (start_row, start_col),
                            (row, col),
                            self.board[row][col]
                        )
                        
                        if len(self.move_history) == 1:
                            self.disable_history_menu()

                    # Reset selected piece
                    self.selected_piece = None
                    
                    # Redraw board
                    self.draw_board()
            
            # If no piece is selected and clicked on own piece, select it
            elif clicked_piece and clicked_piece[0] == self.current_player[0].upper():
                self.selected_piece = (row, col)
                self.highlighted_positions = [(row, col)]  # Initialize highlights with selected piece
                self.draw_board()        


    def make_ai_move(self):
        """Make an AI move using MCTS"""
        self.start_timer()  # Start timer after human move
        
        self.rotate_board = [[None for _ in range(9)] for _ in range(10)]
        self.rotate_single_highlight = []
        
        if len(self.move_history) == 0:
            self.board_copy = [row[:] for row in self.board]
                 
        # Start the AI move in a separate thread to keep UI responsive
        def ai_thread():

            if self.is_checkmate('red') or self.is_checkmate('black'):
                self.game_over = True
                
            if self.is_checkmate(self.current_player):

                self.stop_timer()  # Stop timer when AI starts its move
                self.timer_label.config(text='000')
                
                self.window.after(0, self.handle_game_end)
                self.enable_history_menu()
                self.switch_color_button.config(state=tk.NORMAL)
                return

            else:
                self.switch_color_button.config(state=tk.DISABLED)

            # Get AI's color based on board orientation
            ai_color = 'red' if self.flipped else 'black'
            
            # Get all valid moves for AI's color
            moves = self.get_all_valid_moves(ai_color)
            if not moves:
                if self.is_in_check(ai_color):
                    self.game_over = True
                    self.window.after(0, self.handle_game_end)
                    self.enable_history_menu()
                return
            
            # Create MCTS instance with reference to the game
            mcts = MCTS(self.board, ai_color, time_limit=30.0, flipped=self.flipped, max_mate_depth=30)
            best_move = mcts.get_best_move()

            if best_move:
                # Schedule the move execution on the main thread
                self.window.after(0, lambda: self.execute_ai_move(best_move, ai_color))

        # Start the AI computation in a separate thread
        import threading
        ai_thread = threading.Thread(target=ai_thread)
        ai_thread.daemon = True  # Make thread daemon so it doesn't block program exit
        ai_thread.start()
  

    # YELLOW HIGHTLIGHT(2nd modification)
    def highlight_piece(self, row, col):
        """Draw a yellow highlight around the selected piece"""
        # Calculate position on intersections
        x = self.board_margin + col * self.cell_size
        y = self.board_margin + row * self.cell_size
        
        if self.decrease_size == True:
            self.highlight_radius = self.small_highlight_piece_radius
        else:
            self.highlight_radius = self.piece_radius
        
        # Create a yellow square around the piece
        self.canvas.create_rectangle(
            x - self.highlight_radius - 2,
            y - self.highlight_radius - 2,
            x + self.highlight_radius + 2,
            y + self.highlight_radius + 2,
            outline='yellow',
            width=2,
            tags='highlight'
        )    

        self.decrease_size = False

    def evaluate_piece_safety(self, row, col, piece, color):
        """Evaluate how safe a piece is in its current position"""
        safety_score = 0
        piece_values = {
            '將': 10000, '帥': 10000,
            '車': 900,
            '馬': 400,
            '炮': 500,
            '象': 200, '相': 200,
            '士': 200, '仕': 200,
            '卒': 100, '兵': 100
        }
        
        # Check if the piece is under attack
        is_attacked = False
        defenders = 0
        attackers = 0
        
        # Count attackers and defenders
        for r in range(10):
            for c in range(9):
                checking_piece = self.board[r][c]
                if checking_piece:
                    if checking_piece[0] != color[0].upper():  # Enemy piece
                        # If enemy can capture this piece
                        if self.is_valid_move((r, c), (row, col)):
                            attackers += 1
                            is_attacked = True
                            # Penalty based on value difference
                            if piece_values[checking_piece[1]] < piece_values[piece[1]]:
                                safety_score -= 50  # Extra penalty if threatened by lesser piece
                    else:  # Friendly piece
                        if self.is_valid_move((r, c), (row, col)):
                            defenders += 1
                            safety_score += 20  # Bonus for each defender
        
        # Heavy penalty if attacked and not defended
        if is_attacked and defenders == 0:
            safety_score -= 200
        
        # Bonus for defended pieces
        if defenders > attackers:
            safety_score += 100
            
        return safety_score

    def evaluate_king_safety(self, color):
        """Evaluate king safety and surrounding protection"""
        kings = self.find_kings()
        king_pos = kings[1] if color == 'black' else kings[0]
        if not king_pos:
            return -9999
        
        king_row, king_col = king_pos
        safety = 0
        
        # Check protecting pieces
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                r, c = king_row + dr, king_col + dc
                if 0 <= r < 10 and 0 <= c < 9:
                    piece = self.board[r][c]
                    if piece and piece[0] == color[0].upper():
                        safety += 30
        
        # Penalty for exposed king
        if self.is_in_check(color):
            safety -= 200
        
        return safety

    def get_all_valid_moves(self, color):
        """Get all valid moves for a given color"""
        moves = []
        for from_row in range(10):
            for from_col in range(9):
                piece = self.board[from_row][from_col]
                if piece and piece[0] == color[0].upper():
                    for to_row in range(10):
                        for to_col in range(9):
                            if self.is_valid_move((from_row, from_col), (to_row, to_col)):
                                moves.append(((from_row, from_col), (to_row, to_col)))
        return moves

    def is_checkmate(self, color):
        """
        Check if the given color is in checkmate.
        Returns True if the player has no legal moves to escape check.
        """
        
        
        # Try every possible move for every piece of the current player
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece and piece[0] == color[0].upper():  # If it's current player's piece
                    # Try all possible destinations
                    for to_row in range(10):
                        for to_col in range(9):
                            if self.is_valid_move((row, col), (to_row, to_col)):
                                # Try the move
                                original_piece = self.board[to_row][to_col]
                                self.board[to_row][to_col] = piece
                                self.board[row][col] = None
                                
                                # Check if still in check
                                still_in_check = self.is_in_check(color)
                                
                                # Undo the move
                                self.board[row][col] = piece
                                self.board[to_row][to_col] = original_piece
                                
                                # If any move gets out of check, not checkmate
                                if not still_in_check:
                                    return False
        
        # If no legal moves found, it's checkmate
            
        self.game_over = True  # Add this line

        return True

    def switch_colors(self):
        """Switch the board orientation by rotating it 180 degrees"""
        
        self.flipped = not self.flipped

        self.top_numbers = self.black_numbers if not self.flipped else self.red_numbers_flipped
        self.bottom_numbers = self.red_numbers if not self.flipped else self.black_numbers_flipped
        
        if len(self.move_history) > 0:
            self.check_rotate = not self.check_rotate
            
        self.switch_color_button.destroy()
        
        # Create switch color button
        self.switch_color_button = ttk.Button(
            self.button_frame,
            text="红黑对调",
            command=self.switch_colors,
            width=8,
            style='Custom.TButton'
        )
        self.switch_color_button.pack(pady=5, before=self.restart_button)

        # Store current board state
        current_state = [row[:] for row in self.board]
        current_highlights = self.highlighted_positions[:]
        
        # Clear the board
        self.board = [[None for _ in range(9)] for _ in range(10)]
        
        # Rotate pieces 180 degrees
        for row in range(10):
            for col in range(9):
                if current_state[row][col]:
                    new_row = 9 - row
                    new_col = 8 - col
                    self.board[new_row][new_col] = current_state[row][col]
                    
        self.copy_switch_board = [[None for _ in range(9)] for _ in range(10)]  # Initialize empty board copy

        # Rotate original pieces 180 degrees
        for row in range(10):
            for col in range(9):
                if self.board_copy[row][col]:
                    new_row = 9 - row
                    new_col = 8 - col
                    self.copy_switch_board[new_row][new_col] = self.board_copy[row][col]
        
        self.board_copy = [[None for _ in range(9)] for _ in range(10)]
        self.board_copy = [row[:] for row in self.copy_switch_board]

        # Rotate highlighted positions
        self.highlighted_positions = []
        for pos in current_highlights:
            if pos:
                row, col = pos
                new_row = 9 - row
                new_col = 8 - col
                self.highlighted_positions.append((new_row, new_col))
        
        # Update selected piece position if any
        if self.selected_piece:
            row, col = self.selected_piece
            self.selected_piece = (9 - row, 8 - col)
        
        # Handle piece setting mode without recreating frame
        if self.piece_setting_mode:
            self.piece_to_place = None
            self.selected_instance_id = None
            
            if self.pieces_frame:
                # Clear existing pieces frame contents
                for widget in self.pieces_frame.winfo_children():
                    widget.destroy()
                
                # Create top and bottom frames within existing pieces frame
                top_frame = tk.Frame(self.pieces_frame)
                bottom_frame = tk.Frame(self.pieces_frame)
                top_frame.pack(side=tk.TOP, pady=10)
                bottom_frame.pack(side=tk.BOTTOM, pady=10)
                
                # Create piece sections based on flipped state
                piece_canvas_size = self.cell_size * 6
                if self.flipped:
                    # Red pieces on top when flipped
                    self.red_canvas = self._create_piece_section(top_frame, 'R', piece_canvas_size)
                    self.black_canvas = self._create_piece_section(bottom_frame, 'B', piece_canvas_size)
                else:
                    # Black pieces on top when not flipped
                    self.black_canvas = self._create_piece_section(top_frame, 'B', piece_canvas_size)
                    self.red_canvas = self._create_piece_section(bottom_frame, 'R', piece_canvas_size)
        else:
            if not self.replay_mode:
                
                # Update current player and trigger AI move if needed
                if self.flipped:
                    self.current_player = 'red'
                    if not self.is_checkmate('red') and not self.is_checkmate('black'):
                        self.window.after(100, self.make_ai_move)
                else:
                    self.current_player = 'black'
                    if not self.is_checkmate('red') and not self.is_checkmate('black'):
                        self.window.after(100, self.make_ai_move)
            
        # Redraw the board
        self.draw_board()


    def _create_piece_section(self, frame, color_prefix, canvas_size):
        """Helper function to create piece section within a frame"""
        canvas = tk.Canvas(
            frame,
            width=canvas_size + 5,
            height=self.cell_size * 3 + 5,
            bg='#f0d5b0'
        )
        canvas.pack(padx=5)

        # Define piece layouts
        piece_layout = []
        if color_prefix == 'R':  # Red pieces
            piece_layout = [
                [('R帥',1), ('R仕',1), ('R仕',1), ('R相',1), ('R相',1)],
                [('R兵',1), ('R兵',1), ('R兵',1), ('R兵',1), ('R兵',1)],
                [('R馬',1), ('R馬',1), ('R車',1), ('R車',1), ('R炮',1), ('R炮',1)]
            ]
        else:  # Black pieces
            piece_layout = [
                [('B將',1), ('B士',1), ('B士',1), ('B象',1), ('B象',1)],
                [('B卒',1), ('B卒',1), ('B卒',1), ('B卒',1), ('B卒',1)],
                [('B馬',1), ('B馬',1), ('B車',1), ('B車',1), ('B炮',1), ('B炮',1)]
            ]

        # Draw pieces based on layout
        for row, pieces_row in enumerate(piece_layout):
            for col, piece_info in enumerate(pieces_row):
                if piece_info:
                    piece, _ = piece_info
                    x = col * self.cell_size + self.cell_size // 2 + 4
                    y = row * self.cell_size + self.cell_size // 2 + 4
                    
                    instance_id = f"{piece}_{row}_{col}"
                    self._draw_piece(canvas, x, y, piece, instance_id)

        return canvas

    def _draw_piece(self, canvas, x, y, piece, instance_id):
        """Helper function to draw a piece on the canvas"""
        # Draw piece circle
        circle = canvas.create_oval(
            x - self.piece_radius, y - self.piece_radius,
            x + self.piece_radius, y + self.piece_radius,
            fill='white',
            outline='red' if piece.startswith('R') else 'black',
            width=2,
            tags=(instance_id,)
        )
        
        # Draw piece text
        text = canvas.create_text(
            x, y,
            text=piece[1],
            fill='red' if piece.startswith('R') else 'black',
            font=('KaiTi', 25, 'bold'),
            tags=(instance_id,)
        )
        
        # Bind click event
        for item in [circle, text]:
            canvas.tag_bind(instance_id, '<Button-1>', 
                lambda e, c=canvas, i=instance_id, p=piece: self.select_piece_from_canvas(e, c, i, p))


    def handle_game_end(self):
        """Handle end of game tasks"""
        self.game_over = True
        self.show_centered_warning("游戏结束", "绝 杀 ！")
        # Enable replay button after checkmate
        self.replay_button.config(state=tk.NORMAL)
        self.save_game_to_pgn()

    def set_button_states_for_gameplay(self):
        """Set button states for normal gameplay"""
        self.restart_button.config(state=tk.NORMAL)      # Keep restart button enabled

        # Enable replay button if game is over, disable otherwise
        if self.game_over:
            self.replay_button.config(state=tk.NORMAL)
        else:
            self.replay_button.config(state=tk.DISABLED)
                    
        self.prev_move_button.config(state=tk.DISABLED)  # Disable previous move button
        self.next_move_button.config(state=tk.DISABLED)  # Disable next move button

    def add_move_to_history(self, from_pos, to_pos, piece):
        """Record a move and board state"""
        
        move = {
            'from_pos': from_pos,
            'to_pos': to_pos,
            'piece': piece,
            'board_state': [row[:] for row in self.board]  # Deep copy of board
        }

        if self.move_rotate == True:
            move['board_state'] = [row[:] for row in self.rotate_board]

        self.move_history.append(move)

    def show_centered_warning(self, title, message):
        """Shows a warning messagebox centered on the game board"""
        # Create custom messagebox
        warn_window = tk.Toplevel(self.window)
        warn_window.withdraw()  # Hide window initially
        warn_window.title(title)
        
        # Configure the warning window
        warn_window.transient(self.window)
        warn_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button
        
        def on_ok():
            # If it's a checkmate message, add END to records
            if message == "绝 杀 ！" and self.move_text:
                self.move_text.config(state='normal')
                self.move_text.insert(tk.END, "THE END")
                self.move_text.config(state='disabled')
                self.move_text.see(tk.END)
                self.move_history_records.append("END")
            warn_window.destroy()
        
        # Add message and OK button with custom fonts
        frame = ttk.Frame(warn_window, padding="20 10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            frame, 
            text=message,
            font=('SimSun', 12),
            wraplength=260
        ).pack(pady=(0, 10))
        
        ttk.Button(
            frame,
            text="OK",
            command=on_ok,
            width=10
        ).pack(pady=(0, 10))
        
        # Set fixed size
        warn_window.geometry('300x100')
        warn_window.resizable(False, False)
        
        # Calculate position before showing window
        warn_window.update_idletasks()
        
        # Get the coordinates of the main window and board
        window_x = self.window.winfo_x()
        window_y = self.window.winfo_y()
        board_x = window_x + self.board_frame.winfo_x() + self.canvas.winfo_x()
        board_y = window_y + self.board_frame.winfo_y() + self.canvas.winfo_y()
        
        # Calculate center position
        x = board_x + (self.canvas.winfo_width() - warn_window.winfo_width()) // 2
        y = board_y + (self.canvas.winfo_height() - warn_window.winfo_height()) // 2
        
        # Set position and show window
        warn_window.geometry(f"+{x}+{y}")
        warn_window.grab_set()  # Set modal state before showing
        warn_window.deiconify()  # Show the window
        warn_window.focus_force()  # Force focus
        
        # Wait for window to close
        self.window.wait_window(warn_window)


    def get_piece_position_descriptor(self, from_pos, to_pos, piece, current_board=None):
        """
        Determine 前/后 based on piece positions.
        current_board parameter allows passing the correct board state.
        """
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        piece_color = piece[0]
        piece_type = piece[1]
        
        # Use provided board state or default to self.board
        board_to_use = current_board if current_board is not None else self.board
        
        # Find all identical pieces in the same column
        identical_positions = []
        for row in range(10):
            current_piece = board_to_use[row][from_col]
            if current_piece:
                if piece_type == '馬' and current_piece[0] == piece_color and current_piece[1] == piece_type:
                    identical_positions.append(row)
                else:
                    if not current_board:
                        if current_piece[0] == piece_color and current_piece[1] == piece_type and row != to_row:
                            identical_positions.append(row)
                    else:
                        if current_piece[0] == piece_color and current_piece[1] == piece_type:
                            identical_positions.append(row)
        if not current_board:
            identical_positions.append(from_row)

        # If there are two identical pieces in the same column
        if len(identical_positions) == 2:
            if self.flipped == False:
                if piece_color == 'R':
                    return "前" if from_row == min(identical_positions) else "后"
                else:
                    return "后" if from_row == min(identical_positions) else "前"
            else:
                if piece_color == 'R':
                    return "后" if from_row == min(identical_positions) else "前"
                else:
                    return "前" if from_row == min(identical_positions) else "后"
                         
        return ""

    def get_move_text(self, from_pos, to_pos, piece, current_board=None):
        """
        Convert a move into Chinese chess notation, accounting for board orientation.
        Adjusts move notation based on the visual perspective of each side.
        """
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece_name = piece[1]
        piece_color = piece[0]
        
        # Get column numbers based on piece color and board orientation
        if piece_color == 'R':
            columns = ['一', '二', '三', '四', '五', '六', '七', '八', '九']
            if not self.flipped:
                # Playing from bottom, count from right to left
                from_col_text = columns[8 - from_col]
                to_col_text = columns[8 - to_col]
            else:
                # Playing from top, count from left to right
                from_col_text = columns[from_col]
                to_col_text = columns[to_col]
        else:  # Black pieces
            columns = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
            if not self.flipped:
                # Playing from bottom, count from left to right
                from_col_text = columns[from_col]
                to_col_text = columns[to_col]
            else:
                # Playing from top, count from right to left
                from_col_text = columns[8 - from_col]
                to_col_text = columns[8 - to_col]
        
        # Get position descriptor (前/后)
        position_descriptor = self.get_piece_position_descriptor(from_pos, to_pos, piece, current_board)
        
        # Determine direction based on visual perspective
        if piece_color == 'R':
            # Playing from bottom perspective
            if not self.flipped:

                if to_row < from_row:
                    direction = '进'
                elif to_row > from_row:
                    direction = '退'
                else:
                    direction = '平'

            else:
            
                # Playing from top perspective
                if to_row > from_row:
                    direction = '进'
                elif to_row < from_row:
                    direction = '退'
                else:
                    direction = '平'
            
        else:
            if not self.flipped:

                # Playing from top perspective
                if to_row > from_row:
                    direction = '进'
                elif to_row < from_row:
                    direction = '退'
                else:
                    direction = '平'
            else:
                
                if to_row < from_row:
                    direction = '进'
                elif to_row > from_row:
                    direction = '退'
                else:
                    direction = '平'
                    
        # Calculate steps based on visual perspective
        steps = abs(to_row - from_row)

        if piece_color == 'R':

            steps_text = columns[steps-1] if steps > 0 else to_col_text
        else:
            steps_text = str(steps) if steps > 0 else to_col_text

        # Construct move text
        if position_descriptor and piece_name not in ['仕', '士', '相', '象']:
            if piece_name == '馬':
                move_text = f"{position_descriptor}{piece_name}{direction}{to_col_text}"
            else:
                move_text = f"{position_descriptor}{piece_name}{direction}{steps_text}"
        else:
            if piece_name in ['兵', '卒', '帥', '將', '車', '炮']:
                move_text = f"{piece_name}{from_col_text}{direction}{steps_text}"
            else:
                move_text = f"{piece_name}{from_col_text}{direction}{to_col_text}"
        
        return move_text

    def add_move_to_records(self, from_pos, to_pos, piece):
        """Add a move to the current game history"""
        move_text = self.get_move_text(from_pos, to_pos, piece)
        self.move_history_records.append(f"{move_text}")
        self.update_records_display()

    def update_records_display(self):
        """Update the records display if it exists"""
        if self.move_text and self.move_history_records:
            self.move_text.config(state='normal')
            self.move_text.delete('1.0', tk.END)
            for i, move in enumerate(self.move_history_records, 1):
                if (i + 1) % 2 == 0:
                    sequence_number = int((i + 1) / 2)
                    self.move_text.insert(tk.END, f"{sequence_number}. {move}\n")
                else:
                    take_up_space = ''
                    for i in range(len(str(sequence_number))):
                        take_up_space += ' '
                    self.move_text.insert(tk.END, f"{take_up_space}  {move}\n")
            self.move_text.config(state='disabled')
            self.move_text.see(tk.END)  # Scroll to the bottom


    def toggle_records(self):
        """Toggle the visibility of the records frame"""

        self.records_seen = not self.records_seen
        
        self.records_button.destroy()
        self.records_button = ttk.Button(
            self.button_frame,
            text="隐藏棋谱" if self.records_seen == True else "打开棋谱",
            command=self.toggle_records,
            width=8,
            style='Custom.TButton'
        )
        self.records_button.pack(pady=5, before=self.switch_color_button)

        # Handle the records frame visibility
        if self.records_frame.winfo_ismapped():
            self.records_frame.pack_forget()
            
            # If in piece setting mode, ensure pieces frame is visible
            if self.piece_setting_mode and self.pieces_frame:
                self.pieces_frame.pack(side=tk.RIGHT, padx=10)
        else:
            # Pack the records frame at the start of main_frame
            self.records_frame.pack(side=tk.LEFT, before=self.board_frame, padx=10)
            
            # If in piece setting mode and pieces frame exists, repack it
            if self.piece_setting_mode and self.pieces_frame:
                self.pieces_frame.pack_forget()
                self.pieces_frame.pack(side=tk.RIGHT, padx=10)
            
            # Bind click event to the move text widget
            self.move_text.bind('<Button-1>', self.on_record_click)

    def sound_effect(self,):
        self.sound_effect_on = not self.sound_effect_on

        self.turn_off_sound_effect.destroy()
        self.turn_off_sound_effect = ttk.Button(
            self.button_frame,
            
            text="关闭音效" if self.sound_effect_on == True else "打开音效",
            command=self.sound_effect,
            width=8,
            style='Custom.TButton'
        )
        self.turn_off_sound_effect.pack(pady=5, before=self.records_button)

    def highlight_current_move(self, move_index):
        """Highlight the current move in the records display"""
        if self.move_text:
            # Clear any existing highlights
            self.move_text.tag_remove('highlight', '1.0', tk.END)
            
            if 0 <= move_index < len(self.move_history_records):
                # Calculate the line number (1-based index)
                line_number = move_index + 1
                
                # Create position strings for the start and end of the line
                start_pos = f"{line_number}.0"
                end_pos = f"{line_number + 1}.0"
                
                # Add highlight tag to the current move line
                self.move_text.tag_add('highlight', start_pos, end_pos)
                
                # Configure the highlight tag with blue background
                self.move_text.tag_configure('highlight', background='light blue')
                
                # Make sure the highlighted line is visible
                self.move_text.see(start_pos)

    def next_replay_move(self):
        """Show next move in replay"""
        if not self.replay_mode or self.current_replay_index >= len(self.move_history):
            self.end_replay()
            return
            
        move = self.move_history[self.current_replay_index]
        # Restore board state
        for i in range(len(self.board)):
            self.board[i] = move['board_state'][i][:]
    
        # Highlight the move
        self.highlighted_positions = [move['from_pos'], move['to_pos']]
        
        if self.move_history_numbers[self.current_replay_index]:
            self.top_numbers = self.move_history_numbers[self.current_replay_index][0]
            self.bottom_numbers = self.move_history_numbers[self.current_replay_index][1]
        
        # Highlight the corresponding move in the records
        self.highlight_current_move(self.current_replay_index)
        
        self.current_replay_index += 1
        
        # Enable previous button as we're not at the start
        self.prev_move_button.config(state=tk.NORMAL)
        
        if self.current_replay_index == len(self.move_history):

            self.next_move_button.destroy()
            # Create next move button (initially disabled)
            self.next_move_button = ttk.Button(
                self.button_frame,
                text="下一步",
                command=self.next_replay_move,
                width=8,
                style='Custom.TButton',
                state=tk.DISABLED
            )
            self.next_move_button.pack(pady=5)

        elif self.current_replay_index < len(self.move_history):
            
            self.next_move_button.destroy()
            # Create next move button (initially disabled)
            self.next_move_button = ttk.Button(
                self.button_frame,
                text="下一步",
                command=self.next_replay_move,
                width=8,
                style='Custom.TButton',
            )
            self.next_move_button.pack(pady=5)
        
        self.draw_board()

    def prev_replay_move(self):
        """Show previous move in replay"""
        if not self.replay_mode or self.current_replay_index <= 0:
            return
            
        self.current_replay_index -= 1
        
        # If at the beginning, disable prev button
        if self.current_replay_index == 0:
            self.prev_move_button.config(state=tk.DISABLED)
            
            # Clear highlight when at start
            if self.move_text:
                self.move_text.tag_remove('highlight', '1.0', tk.END)
        else:
            # Highlight the corresponding move in the records
            self.highlight_current_move(self.current_replay_index - 1)
        
        if self.current_replay_index > 0:

            self.prev_move_button.destroy()
            # Create previous move button (initially disabled)
            self.prev_move_button = ttk.Button(
                self.button_frame,
                text="上一步",
                command=self.prev_replay_move,
                width=8,
                style='Custom.TButton',
            )
            self.prev_move_button.pack(pady=5, before=self.next_move_button)

        elif self.current_replay_index == 0:
            
            self.prev_move_button.destroy()
            # Create previous move button (initially disabled)
            self.prev_move_button = ttk.Button(
                self.button_frame,
                text="上一步",
                command=self.prev_replay_move,
                width=8,
                style='Custom.TButton',
                state=tk.DISABLED
            )
            self.prev_move_button.pack(pady=5, before=self.next_move_button)

        # Always enable next button when we go back
        self.next_move_button.config(state=tk.NORMAL)
        
        # If there are moves to show, display the board state at that index
        if self.current_replay_index > 0:
            move = self.move_history[self.current_replay_index - 1]
            # Restore board state
            for i in range(len(self.board)):
                self.board[i] = move['board_state'][i][:]
        else:
            # If we're at the beginning, show initial board
                
            self.board = [row[:] for row in self.board_copy]
            self.draw_board()

        
        # Update highlights if not at the beginning
        if self.current_replay_index > 0:
            move = self.move_history[self.current_replay_index - 1]
            self.highlighted_positions = [move['from_pos'], move['to_pos']]
        else:
            self.highlighted_positions = []
        

        if self.move_history_numbers[self.current_replay_index]:
            self.top_numbers = self.move_history_numbers[self.current_replay_index][0]
            self.bottom_numbers = self.move_history_numbers[self.current_replay_index][1]
        
        self.draw_board()

    def start_replay(self):
        """Start replay mode"""

        if not self.move_history:
            self.show_centered_warning("提示", "没有可以回放的历史记录")
            return
            
        if self.records_seen == False:
            self.toggle_records()
        else:
            pass

        self.replay_button.destroy()
        # Create replay button
        self.replay_button = ttk.Button(
            self.button_frame,
            text="复盘",
            command=self.start_replay,
            width=8,
            style='Custom.TButton'
        )
        self.replay_button.pack(pady=5, before=self.prev_move_button)

        self.replay_mode = True
        self.current_replay_index = 0
        self.highlighted_positions = []  # Clear all highlights

        # Clear any existing text highlights
        if self.move_text:
            self.move_text.tag_remove('highlight', '1.0', tk.END)

        # Disable normal game buttons during replay
        self.replay_button.config(state=tk.DISABLED)
        self.next_move_button.config(state=tk.NORMAL)
        self.prev_move_button.config(state=tk.DISABLED)
        
        self.board = [row[:] for row in self.board_copy]
        self.draw_board()

        if self.move_history_numbers[0][1][0] not in self.bottom_numbers:
                
            self.rotate_move_history = []
            self.rotate_move_history_numbers = []

            for numbers in self.move_history_numbers:
                top_numbers = []
                bottom_numbers = []
                top_numbers[:] = numbers[1][:]
                bottom_numbers[:] = numbers[0][:]
                top_numbers.reverse()
                bottom_numbers.reverse()
                self.rotate_move_history_numbers.append([top_numbers, bottom_numbers])

            self.board = [[None for _ in range(9)] for _ in range(10)]
            self.highlighted_positions = []

            for move in self.move_history:
                self.board = [row[:] for row in move['board_state']]
                self.highlighted_positions = [move['from_pos'], move['to_pos']]
                self.rotate_to_replay()
                        
                new_move = {
                    'from_pos': self.rotate_single_highlight[0],
                    'to_pos': self.rotate_single_highlight[1],
                    'piece': move['piece'],
                    'board_state': [row[:] for row in self.rotate_board]  # Deep copy of board
                }

                self.rotate_move_history.append(new_move)

            self.move_history = self.rotate_move_history
            self.move_history_numbers = self.rotate_move_history_numbers

    def end_replay(self):
        """End replay mode"""
        self.replay_mode = False
        self.current_replay_index = 0

        # Set button states for normal gameplay
        self.set_button_states_for_gameplay()
        
        self.initialize_board()
        self.draw_board()
        
    def initialize_board(self):
        # Initialize empty board
        self.board = [[None for _ in range(9)] for _ in range(10)]
        
        # Set up initial piece positions
        self.setup_pieces()
                
    def setup_pieces(self):
        # Red pieces
        red_pieces = {
            (9, 0): 'R車', (9, 1): 'R馬', (9, 2): 'R相',
            (9, 3): 'R仕', (9, 4): 'R帥', (9, 5): 'R仕',
            (9, 6): 'R相', (9, 7): 'R馬', (9, 8): 'R車',
            (7, 1): 'R炮', (7, 7): 'R炮',
            (6, 0): 'R兵', (6, 2): 'R兵', (6, 4): 'R兵',
            (6, 6): 'R兵', (6, 8): 'R兵'
        }
        
        # Black pieces (AI)
        black_pieces = {
            (0, 0): 'B車', (0, 1): 'B馬', (0, 2): 'B象',
            (0, 3): 'B士', (0, 4): 'B將', (0, 5): 'B士',
            (0, 6): 'B象', (0, 7): 'B馬', (0, 8): 'B車',
            (2, 1): 'B炮', (2, 7): 'B炮',
            (3, 0): 'B卒', (3, 2): 'B卒', (3, 4): 'B卒',
            (3, 6): 'B卒', (3, 8): 'B卒'
        }
        
        # Place pieces on board based on orientation
        if not self.flipped:
            # Normal orientation (red at bottom)
            for pos, piece in red_pieces.items():
                row, col = pos
                self.board[row][col] = piece
            for pos, piece in black_pieces.items():
                row, col = pos
                self.board[row][col] = piece
        else:
            # Flipped orientation (black at bottom)
            for pos, piece in red_pieces.items():
                row, col = pos
                self.board[9 - row][col] = piece
            for pos, piece in black_pieces.items():
                row, col = pos
                self.board[9 - row][col] = piece

    def draw_board(self):
        # Clear canvas
        self.canvas.delete("all")
        
        # Draw the outer border
        self.canvas.create_rectangle(
            self.board_margin, self.board_margin,
            self.canvas_width - self.board_margin,
            self.canvas_height - self.board_margin,
            width=1
        )

        self.canvas.create_rectangle(
            self.board_margin - 5, self.board_margin - 5,
            self.canvas_width - self.board_margin + 6,
            self.canvas_height - self.board_margin + 6,
            width=2
        )

        # clear hightlight(3rd modification)
        self.canvas.delete('highlight')

        # add hightlight(4th modification)
        if self.selected_piece:
            row, col = self.selected_piece
            self.highlight_piece(row, col)

        # Draw grid lines
        for i in range(10):  # Horizontal lines
            y = self.board_margin + i * self.cell_size
            self.canvas.create_line(
                self.board_margin, y,
                self.canvas_width - self.board_margin, y
            )
            
        for i in range(9):  # Vertical lines
            x = self.board_margin + i * self.cell_size
            # Draw vertical lines with river gap
            self.canvas.create_line(
                x, self.board_margin,
                x, self.board_margin + 4 * self.cell_size
            )
            self.canvas.create_line(
                x, self.board_margin + 5 * self.cell_size,
                x, self.canvas_height - self.board_margin
            )

        # Draw palace diagonal lines
        # Top palace
        self.canvas.create_line(
            self.board_margin + 3 * self.cell_size, self.board_margin,
            self.board_margin + 5 * self.cell_size, self.board_margin + 2 * self.cell_size
        )
        self.canvas.create_line(
            self.board_margin + 5 * self.cell_size, self.board_margin,
            self.board_margin + 3 * self.cell_size, self.board_margin + 2 * self.cell_size
        )
        
        # Bottom palace
        self.canvas.create_line(
            self.board_margin + 3 * self.cell_size, self.canvas_height - self.board_margin - 2 * self.cell_size,
            self.board_margin + 5 * self.cell_size, self.canvas_height - self.board_margin
        )
        self.canvas.create_line(
            self.board_margin + 5 * self.cell_size, self.canvas_height - self.board_margin - 2 * self.cell_size,
            self.board_margin + 3 * self.cell_size, self.canvas_height - self.board_margin
        )

        # Draw river text
        river_y = self.board_margin + 4.5 * self.cell_size
        self.canvas.create_text(
            self.canvas_width / 2, river_y,
            text="楚   河        漢   界",
            font=('KaiTi', 23)
        )
        
        # Draw pieces on intersections
        for row in range(10):
            for col in range(9):
                if self.board[row][col]:
                    # Calculate position on intersections
                    x = self.board_margin + col * self.cell_size
                    y = self.board_margin + row * self.cell_size
                    
                    # Draw piece circle
                    color = 'red' if self.board[row][col][0] == 'R' else 'black'
                    self.canvas.create_oval(
                        x - self.piece_radius, y - self.piece_radius,
                        x + self.piece_radius, y + self.piece_radius,
                        fill='white',
                        outline=color,
                        width=2
                    )
                    
                    # Draw piece text
                    piece_text = self.board[row][col][1]
                    text_color = 'red' if self.board[row][col][0] == 'R' else 'black'
                    self.canvas.create_text(
                        x, y,
                        text=piece_text,
                        fill=text_color,
                        font=('KaiTi', 25, 'bold')
                    )
            
        # Modify the highlight section to show all highlighted positions
        self.canvas.delete('highlight')
        for pos in self.highlighted_positions:
            row, col = pos
            self.highlight_piece(row, col)

        # Draw top numbers
        for col, num in enumerate(self.top_numbers):
            x = self.board_margin + col * self.cell_size
            y = self.board_margin - 37
            self.canvas.create_text(
                x, y,
                text=num,
                fill='black',
                font=('Arial', 12)
            )

        # Draw bottom numbers
        for col, num in enumerate(self.bottom_numbers):
            x = self.board_margin + col * self.cell_size
            y = self.canvas_height - self.board_margin + 37
            self.canvas.create_text(
                x, y,
                text=num,
                fill='black',
                font=('Arial', 12)
            )

    def restart_game(self):

        self.stop_timer()  # Stop timer when AI starts its move
        self.timer_label.config(text='000')
        self.disable_history_menu()

        self.check_rotate = False
        self.rotate_board = [[None for _ in range(9)] for _ in range(10)]
        self.rotate_single_highlight = []
        self.rotate_replay_board = []
        self.move_history_numbers = []
        
        self.switch_color_button.config(state=tk.NORMAL)
        self.restart_button.destroy()
        # Create restart button
        self.restart_button = ttk.Button(
            self.button_frame,
            text="再来一盘",  # Keep the original Chinese text
            command=self.restart_game,
            width=8,
            style='Custom.TButton'
        )
        self.restart_button.pack(pady=5, before=self.replay_button)

        self.restart_state = True
            
        # Store the current game's move history if it exists
        if self.move_history:
            self.game_history.append(self.move_history)
        self.move_history = []
        self.move_history_records = []  # Clear the records list
        
        # Reset game state
        self.selected_piece = None
        self.highlighted_positions = []
        self.current_player = 'red'
        self.replay_mode = False
        self.current_replay_index = 0            
        self.game_over = False
                    
        # Set button states for normal gameplay
        self.set_button_states_for_gameplay()
                
        # Clear the records display
        if self.move_text:
            self.move_text.config(state='normal')
            self.move_text.delete('1.0', tk.END)
            self.move_text.config(state='disabled')
        
        self.board = [row[:] for row in self.board_copy]
        self.draw_board()

        # If the board is flipped, set current player to red and trigger immediate AI move
        if self.flipped:
            self.current_player = 'red'  # Set to red so AI plays as red
            self.window.after(100, self.make_ai_move)  # Small delay to ensure board is redrawn first


    # Add piece movement validation(8 functions)

    def is_valid_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        # Basic validation
        if not (0 <= to_row < 10 and 0 <= to_col < 9):
            return False
            
        # Can't capture own pieces
        if self.board[to_row][to_col] and self.board[to_row][to_col][0] == piece[0]:
            return False
        
        # Get piece type (second character of the piece string)
        piece_type = piece[1]
        
        # Check specific piece movement rules
        if piece_type == '帥' or piece_type == '將':  # General/King
            return self.is_valid_general_move(from_pos, to_pos)
        elif piece_type == '仕' or piece_type == '士':  # Advisor
            return self.is_valid_advisor_move(from_pos, to_pos)
        elif piece_type == '相' or piece_type == '象':  # Elephant
            return self.is_valid_elephant_move(from_pos, to_pos)
        elif piece_type == '馬':  # Horse
            return self.is_valid_horse_move(from_pos, to_pos)
        elif piece_type == '車':  # Chariot
            return self.is_valid_chariot_move(from_pos, to_pos)
        elif piece_type == '炮':  # Cannon
            return self.is_valid_cannon_move(from_pos, to_pos)
        elif piece_type == '兵' or piece_type == '卒':  # Pawn
            return self.is_valid_pawn_move(from_pos, to_pos)
        
        return False

    def is_valid_general_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        # Check if move is within palace (3x3 grid)
        if piece[0] == 'R':  # Red general
            if not self.flipped:

                if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                    return False
            else:

                if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                    return False
            
        else:  # Black general
            if not self.flipped:
                    
                if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                    return False
            else:
                    
                if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                    return False
        
        # Can only move one step horizontally or vertically
        if abs(to_row - from_row) + abs(to_col - from_col) != 1:
            return False
            
        return True

    def is_valid_advisor_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        # Check if move is within palace
        if piece[0] == 'R':  # Red advisor
            if not self.flipped:
                    
                if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                    return False
            else:
                    
                if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                    return False
        else:  # Black advisor
            if not self.flipped:
                    
                if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                    return False
            else:
                    
                if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                    return False
        
        # Must move exactly one step diagonally
        if abs(to_row - from_row) != 1 or abs(to_col - from_col) != 1:
            return False
            
        return True

    def is_valid_elephant_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        # Cannot cross river
        if piece[0] == 'R':  # Red elephant
            if not self.flipped:
                    
                if to_row < 5:  # Cannot cross river
                    return False
            else:
                    
                if to_row > 4:  # Cannot cross river
                    return False
        else:  # Black elephant
            if not self.flipped:
                    
                if to_row > 4:  # Cannot cross river
                    return False
            else:
                    
                if to_row < 5:  # Cannot cross river
                    return False
        
        # Must move exactly two steps diagonally
        if abs(to_row - from_row) != 2 or abs(to_col - from_col) != 2:
            return False
        
        # Check if there's a piece blocking the elephant's path
        blocking_row = (from_row + to_row) // 2
        blocking_col = (from_col + to_col) // 2
        if self.board[blocking_row][blocking_col]:
            return False
            
        return True

    def is_valid_horse_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Must move in an L-shape (2 steps in one direction, 1 step in perpendicular direction)
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        if not ((row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)):
            return False
        
        # Check for blocking piece
        if row_diff == 2:
            blocking_row = from_row + (1 if to_row > from_row else -1)
            if self.board[blocking_row][from_col]:
                return False
        else:
            blocking_col = from_col + (1 if to_col > from_col else -1)
            if self.board[from_row][blocking_col]:
                return False
                
        return True

    def is_valid_chariot_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Must move horizontally or vertically
        if from_row != to_row and from_col != to_col:
            return False
        
        # Check if path is clear
        if from_row == to_row:  # Horizontal move
            start_col = min(from_col, to_col) + 1
            end_col = max(from_col, to_col)
            for col in range(start_col, end_col):
                if self.board[from_row][col]:
                    return False
        else:  # Vertical move
            start_row = min(from_row, to_row) + 1
            end_row = max(from_row, to_row)
            for row in range(start_row, end_row):
                if self.board[row][from_col]:
                    return False
                    
        return True

    def is_valid_cannon_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Must move horizontally or vertically
        if from_row != to_row and from_col != to_col:
            return False
        
        # Count pieces between from and to positions
        pieces_between = 0
        if from_row == to_row:  # Horizontal move
            start_col = min(from_col, to_col) + 1
            end_col = max(from_col, to_col)
            for col in range(start_col, end_col):
                if self.board[from_row][col]:
                    pieces_between += 1
        else:  # Vertical move
            start_row = min(from_row, to_row) + 1
            end_row = max(from_row, to_row)
            for row in range(start_row, end_row):
                if self.board[row][from_col]:
                    pieces_between += 1
        
        # If capturing, need exactly one piece between
        if self.board[to_row][to_col]:
            return pieces_between == 1
        # If not capturing, path must be clear
        return pieces_between == 0

    def is_valid_pawn_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        if piece[0] == 'R':  # Red pawn

            if not self.flipped:

                # Before crossing river
                if from_row > 4:
                    # Can only move forward (up)
                    return to_col == from_col and to_row == from_row - 1
                # After crossing river
                else:
                    # Can move forward or sideways
                    return (to_col == from_col and to_row == from_row - 1) or \
                        (to_row == from_row and abs(to_col - from_col) == 1)
            else:
                # Before crossing river
                if from_row < 5:
                    # Can only move forward (down)
                    return to_col == from_col and to_row == from_row + 1
                # After crossing river
                else:
                    # Can move forward or sideways
                    return (to_col == from_col and to_row == from_row + 1) or \
                        (to_row == from_row and abs(to_col - from_col) == 1)
        else:  # Black pawn
            if not self.flipped:

                # Before crossing river
                if from_row < 5:
                    # Can only move forward (down)
                    return to_col == from_col and to_row == from_row + 1
                
                # After crossing river
                else:
                    # Can move forward or sideways
                    return (to_col == from_col and to_row == from_row + 1) or \
                        (to_row == from_row and abs(to_col - from_col) == 1)
            else:
                # Before crossing river
                if from_row > 4:
                    # Can only move forward (up)
                    return to_col == from_col and to_row == from_row - 1
                # After crossing river
                else:
                    # Can move forward or sideways
                    return (to_col == from_col and to_row == from_row - 1) or \
                        (to_row == from_row and abs(to_col - from_col) == 1)


    def find_kings(self):
        """Find positions of both kings/generals"""
        red_king_pos = black_king_pos = None
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece:
                    if piece[1] == '帥':
                        red_king_pos = (row, col)
                    elif piece[1] == '將':
                        black_king_pos = (row, col)
        return red_king_pos, black_king_pos

    def is_position_under_attack(self, pos, attacking_color):
        """Check if a position is under attack by pieces of the given color"""
        
        # Check from all positions on the board
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece and piece[0] == attacking_color[0].upper():
                    # Check if this piece can move to the target position
                    if self.is_valid_move((row, col), pos):
                        return True
        return False  

    def is_generals_facing(self):
        """Check if the two generals are facing each other directly"""
        red_king_pos, black_king_pos = self.find_kings()
        
        # If either king is missing, return False
        if not red_king_pos or not black_king_pos:
            return False
            
        red_row, red_col = red_king_pos
        black_row, black_col = black_king_pos
        
        # Check if generals are in the same column
        if red_col != black_col:
            return False
            
        # Check if there are any pieces between the generals
        start_row = min(red_row, black_row) + 1
        end_row = max(red_row, black_row)
        
        for row in range(start_row, end_row):
            if self.board[row][red_col]:  # If there's any piece between
                return False
                
        # If we get here, the generals are facing each other
        return True

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

    def run(self):
        self.window.mainloop()

# Create and run the game
if __name__ == "__main__":
    game = ChineseChess()
    game.run()