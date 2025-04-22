

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

        self.escape_positions_table = {}  # New table for caching opponent escape positions

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
                self.mate_transposition_table[key] = [move]
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
        self.escape_positions_table.clear()  # Add this
        
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
