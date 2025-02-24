
import tkinter as tk

from tkinter import ttk


import os
import pygame.mixer

class ChineseChess:

    def __init__(self):
           
        # Add at the beginning of __init__
        self.piece_setting_mode = False
        self.piece_to_place = None
        self.pieces_frame = None
        self.source_canvas = None  # Track which canvas the selected piece is from
        self.records_hidden_by_piece_set = False     
        self.board_copy = [[None for _ in range(9)] for _ in range(10)]  # Initialize empty board copy
        self.copy_switch_board = [[None for _ in range(9)] for _ in range(10)]  # Initialize empty board copy

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

     
        # Add this before other initializations
        self.piece_attributes = {
            '將': [10000, 1, 50],  # King: High value, low attack, high penalty for early moves
            '帥': [10000, 1, 50],
            '車': [900, 9, 0],     # Chariot: High value, high attack, no early move penalty
            '馬': [400, 7, 0],     # Horse: Medium value, high attack, no early move penalty
            '炮': [500, 8, 0],     # Cannon: Medium-high value, high attack, no early move penalty
            '象': [200, 3, 10],    # Elephant: Low value, low attack, small early move penalty
            '相': [200, 3, 10],
            '士': [200, 2, 20],    # Advisor: Low value, very low attack, medium early move penalty
            '仕': [200, 2, 20],
            '卒': [100, 2, 0],     # Pawn: Low value, low attack, no early move penalty
            '兵': [100, 2, 0]
        }
        # Rest of your initialization code...

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
        
        self.window.title("Chinese Chess 7.0.19 (restart ok even color switched, height resizable, spaces ok)")
           
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
        self.records_frame = tk.Frame(self.main_frame)
        
        # Create move history display
        self.move_text = tk.Text(
            self.records_frame,
            font=("SimSun", 12),
            spacing1=3, spacing3=3,
            width=20,
            height=25,
            state='disabled'
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
        self.button_frame.pack(side=tk.LEFT, padx=10)  # Add padding between board and button


        self.records_button = ttk.Button(
            self.button_frame,
            text="棋谱记录",
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
            text="重新开始",
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
            text="摆放棋子" if self.set_pieces_mode == False else "完成摆放",
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
        self.draw_board()
                    
        # Bind mouse event
        self.canvas.bind('<Button-1>', self.on_click)


    def start_new_game(self):

        self.switch_color_button.config(state=tk.NORMAL)
        self.new_game_button.destroy()
        self.new_game_button = ttk.Button(
            self.button_frame,
            text="重新开始",
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

    def toggle_piece_setting_mode(self):
        """Toggle between normal game mode and piece setting mode"""
        self.piece_setting_mode = not self.piece_setting_mode
        self.restart_state = False
        self.replay_mode = False
        self.prev_move_button.config(state=tk.DISABLED)
        self.next_move_button.config(state=tk.DISABLED)

        self.set_pieces_button.destroy()
        
        # Create set pieces button
        self.set_pieces_button = ttk.Button(
            self.button_frame,
            text="摆放棋子" if self.set_pieces_mode == False else "完成摆放",
            command=self.toggle_piece_setting_mode,
            width=8,
            style='Custom.TButton'
        )
        self.set_pieces_button.pack(pady=5, before=self.new_game_button)

        
        if self.records_seen == True and self.piece_setting_mode == True:
            self.toggle_records()
            self.records_hidden_by_piece_set = True
        if self.records_hidden_by_piece_set == True and self.piece_setting_mode == False:
            self.toggle_records()
            self.records_hidden_by_piece_set = False

        if self.piece_setting_mode == False:
            
            self.game_over = False

            # Store the current game's move history if it exists
            if self.move_history:
                self.game_history.append(self.move_history)
            self.move_history = []
            self.move_history_records = []  # Clear the records list
            
            # Clear the records display
            if self.move_text:
                self.move_text.config(state='normal')
                self.move_text.delete('1.0', tk.END)
                self.move_text.config(state='disabled')
            
        if self.piece_setting_mode == False and self.flipped == False:
            self.current_player = 'red'
            
        if self.piece_setting_mode:
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
            
            # Change button text
            self.set_pieces_button.config(text="完成摆放")

        else:
            # Pack the pieces frame with padding
            self.pieces_frame.pack(side=tk.RIGHT, padx=5)
            
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



    def on_click(self, event):

        if len(self.move_history) == 0:
            self.board_copy = [row[:] for row in self.board]

        if self.piece_setting_mode:
            # Convert click coordinates to board position
            col = round((event.x - self.board_margin) / self.cell_size)
            row = round((event.y - self.board_margin) / self.cell_size)
            
            # Ensure click is within board bounds
            if 0 <= row < 10 and 0 <= col < 9 and self.piece_to_place:
                # Place the piece
                self.board[row][col] = self.piece_to_place
                
                # Remove the piece from the canvas
                if self.source_canvas and self.selected_instance_id:
                    # Delete the piece and its highlight
                    self.source_canvas.delete(self.selected_instance_id)
                    self.source_canvas.delete('highlight')
                    
                self.highlighted_positions = [(row, col)]
                self.draw_board()
                
                # Reset selection
                self.piece_to_place = None
                self.selected_instance_id = None
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
                        # Add this line to record the move
                        self.add_move_to_history(
                            (start_row, start_col),
                            (row, col),
                            self.board[row][col]
                        )

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
        import time
        
        if len(self.move_history) == 0:
            self.board_copy = [row[:] for row in self.board]
                            
        if self.is_checkmate('red') or self.is_checkmate('black'):
            self.game_over = True
        start_time = time.time()
        max_time = 5.0  # Reduced from 10.0 to make moves faster
                        
        best_score = float('-inf')
        best_move = None
        best_moving_piece = None
        
        # Get AI's color based on board orientation
        ai_color = 'red' if self.flipped else 'black'
        
        # Get all valid moves for AI's color
        moves = self.get_all_valid_moves(ai_color)
        if not moves:
            # Add this check to handle stalemate or other end conditions
            if self.is_in_check(ai_color):
                self.game_over = True
                self.handle_game_end()
            return
                
        # Sort moves by preliminary evaluation
        moves.sort(key=self._move_sorting_score, reverse=True)
        
        # Check if opponent is in check
        opponent_color = 'black' if ai_color == 'red' else 'red'
        is_check = self.is_in_check(opponent_color)
        max_depth = 6 if is_check else 4  # Search deeper when opponent is in check
        
        # Iterative deepening
        for search_depth in range(2, max_depth + 1):
            if time.time() - start_time > max_time:
                break
            
            alpha = float('-inf')
            beta = float('inf')
            
            for from_pos, to_pos in moves:
                if time.time() - start_time > max_time:
                    break
                
                moving_piece = self.board[from_pos[0]][from_pos[1]]
                captured_piece = self.board[to_pos[0]][to_pos[1]]
                
                # Make temporary move
                self.board[to_pos[0]][to_pos[1]] = moving_piece
                self.board[from_pos[0]][from_pos[1]] = None
                
                if not self.is_in_check(ai_color):
                    score = self.minimax(search_depth - 1, alpha, beta, False)
                    
                    if score > best_score:
                        best_score = score
                        best_move = (from_pos, to_pos)
                        best_moving_piece = moving_piece
                
                # Restore position
                self.board[from_pos[0]][from_pos[1]] = moving_piece
                self.board[to_pos[0]][to_pos[1]] = captured_piece
        
        # Make the best move found
        if best_move:
            from_pos, to_pos = best_move
            # Make the actual move
            self.board[to_pos[0]][to_pos[1]] = best_moving_piece

            self.board[from_pos[0]][from_pos[1]] = None
                                                
            # Play move sound
            if self.sound_effect_on:
                                            
                if hasattr(self, 'move_sound') and self.move_sound:
                    self.move_sound.play()
                                
            # Update game state
            self.highlighted_positions = [from_pos, to_pos]
    
            self.add_move_to_records(from_pos, to_pos, best_moving_piece)

            # Switch to opponent's turn
            self.current_player = opponent_color
                        
            # Add this line to record the AI move
            self.add_move_to_history(from_pos, to_pos, best_moving_piece)

            # Update display
            self.draw_board()
                              
        # Check if the opponent is now in checkmate
        if self.is_checkmate(self.current_player):
            self.handle_game_end()
                        
        # Check if the opponent is now in checkmate
        opponent_color = 'black' if ai_color == 'red' else 'red'
        if not self.is_checkmate(opponent_color):
            self.game_over = False  # Explicitly set game_over to False if not checkmate
       

    
    def minimax(self, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning and simplified evaluation"""
        
        if depth == 0:
            return self.evaluate_position_simple('red' if self.flipped else 'black')
        
        if maximizing_player:
            max_eval = float('-inf')
            moves = self.get_all_valid_moves('black')
            
            for from_pos, to_pos in moves:
                # Store and make move
                moving_piece = self.board[from_pos[0]][from_pos[1]]
                captured_piece = self.board[to_pos[0]][to_pos[1]]
                self.board[to_pos[0]][to_pos[1]] = moving_piece
                self.board[from_pos[0]][from_pos[1]] = None
                
                if not self.is_in_check('black'):
                    eval = self.minimax(depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                
                # Restore position
                self.board[from_pos[0]][from_pos[1]] = moving_piece
                self.board[to_pos[0]][to_pos[1]] = captured_piece
                
                if beta <= alpha:
                    break
            return max_eval if max_eval != float('-inf') else self.evaluate_position_simple()
        else:
            min_eval = float('inf')
            moves = self.get_all_valid_moves('red')
            
            for from_pos, to_pos in moves:
                moving_piece = self.board[from_pos[0]][from_pos[1]]
                captured_piece = self.board[to_pos[0]][to_pos[1]]
                self.board[to_pos[0]][to_pos[1]] = moving_piece
                self.board[from_pos[0]][from_pos[1]] = None
                
                if not self.is_in_check('red'):
                    eval = self.minimax(depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                
                # Restore position
                self.board[from_pos[0]][from_pos[1]] = moving_piece
                self.board[to_pos[0]][to_pos[1]] = captured_piece
                
                if beta <= alpha:
                    break
            return min_eval if min_eval != float('inf') else self.evaluate_position_simple()

    def evaluate_checkmate_potential(self, color):
        """Evaluate how close we are to achieving checkmate"""
        opposing_color = 'red' if color == 'black' else 'black'
        kings = self.find_kings()
        opponent_king_pos = kings[0] if color == 'black' else kings[1]
        score = 0
        
        if not opponent_king_pos:
            return 0
            
        king_row, king_col = opponent_king_pos
        
        # Count attacking pieces near opponent's king
        attackers = 0
        attack_value = 0
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                r, c = king_row + dr, king_col + dc
                if 0 <= r < 10 and 0 <= c < 9:
                    piece = self.board[r][c]
                    if piece and piece[0] == color[0].upper():
                        attackers += 1
                        # Higher value for powerful pieces near the king
                        if piece[1] in ['車', '馬', '炮']:
                            attack_value += 50
                        else:
                            attack_value += 20
        
        score += attackers * 30 + attack_value
        
        # Bonus if opponent's king has limited mobility
        escape_moves = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                r, c = king_row + dr, king_col + dc
                if 0 <= r < 10 and 0 <= c < 9:
                    if (r, c) != (king_row, king_col):
                        if self.is_valid_move((king_row, king_col), (r, c)):
                            # Try the move
                            original_piece = self.board[r][c]
                            self.board[r][c] = self.board[king_row][king_col]
                            self.board[king_row][king_col] = None
                            
                            if not self.is_in_check(opposing_color):
                                escape_moves += 1
                                
                            # Restore the position
                            self.board[king_row][king_col] = self.board[r][c]
                            self.board[r][c] = original_piece
        
        # Higher score when opponent has fewer escape moves
        score += (9 - escape_moves) * 50
        
        # Extra bonus if opponent is in check
        if self.is_in_check(opposing_color):
            score += 200
            
        return score

    def _move_sorting_score(self, move):
        from_pos, to_pos = move
        from_piece = self.board[from_pos[0]][from_pos[1]]
        to_piece = self.board[to_pos[0]][to_pos[1]]
        
        score = 0
        piece_values = {
            '將': 10000, '帥': 10000,
            '車': 900,
            '馬': 400,
            '炮': 500,
            '象': 200, '相': 200,
            '士': 200, '仕': 200,
            '卒': 100, '兵': 100
        }
        
        # Try the move
        original_piece = self.board[to_pos[0]][to_pos[1]]
        self.board[to_pos[0]][to_pos[1]] = from_piece
        self.board[from_pos[0]][from_pos[1]] = None
        
        # Highest priority for checkmate
        if self.is_checkmate('red'):
            score += 10000
        # High priority for check
        elif self.is_in_check('red'):
            score += 1000
            # Additional bonus if the opponent has limited escape moves
            escape_moves = 0
            kings = self.find_kings()
            king_pos = kings[0]  # Red king
            if king_pos:
                king_row, king_col = king_pos
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        r, c = king_row + dr, king_col + dc
                        if 0 <= r < 10 and 0 <= c < 9:
                            if self.is_valid_move((king_row, king_col), (r, c)):
                                escape_moves += 1
            score += (9 - escape_moves) * 100
        
        # Evaluate material gain/loss
        if to_piece:  # Capture move
            score += piece_values[to_piece[1]] * 10
        
        # Position improvement
        if from_piece[1] in ['車', '馬', '炮']:
            if 2 <= to_pos[1] <= 6:  # Central files
                score += 30
            if from_piece[0] == 'B' and to_pos[0] > 4:  # Crossing river
                score += 40
        
        # Restore position
        self.board[from_pos[0]][from_pos[1]] = from_piece
        self.board[to_pos[0]][to_pos[1]] = original_piece
        
        return score

    def evaluate_position_simple(self, color='black'):
        """
        Evaluate board position for the given color.
        color: 'red' or 'black', defaults to 'black' for backward compatibility
        """
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
        
        # Determine which pieces belong to the evaluating side
        eval_prefix = 'R' if color == 'red' else 'B'
        opp_prefix = 'B' if color == 'red' else 'R'
        
        # Material and position evaluation
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece:
                    value = piece_values[piece[1]]
                    position_bonus = 0
                    
                    if piece[1] in ['車', '馬', '炮']:
                        # Bonus for controlling center files
                        if 2 <= col <= 6:
                            position_bonus += 20
                        # Bonus for penetration - adjusted based on color
                        if color == 'red':
                            if row < 5:  # Red pieces advancing
                                position_bonus += 50
                        else:  # black
                            if row > 4:  # Black pieces advancing
                                position_bonus += 50
                    
                    # Calculate piece safety
                    safety_score = self.evaluate_piece_safety(row, col, piece, color)
                    
                    if piece[0] == eval_prefix:  # Our pieces
                        score += value + position_bonus + safety_score
                        if piece[1] in ['卒', '兵']:  # Pawns
                            if color == 'red':
                                if row < 5:  # Crossed river (for red)
                                    score += 50 + (4 - row) * 20
                                else:
                                    score += (9 - row) * 10
                            else:  # black
                                if row > 4:  # Crossed river (for black)
                                    score += 50 + (row - 4) * 20
                                else:
                                    score += row * 10
                    else:  # Opponent's pieces
                        score -= value + position_bonus + safety_score
                        if piece[1] in ['卒', '兵']:
                            if color == 'red':
                                if row > 4:
                                    score -= 50 + (row - 4) * 20
                                else:
                                    score -= row * 10
                            else:  # black
                                if row < 5:
                                    score -= 50 + (4 - row) * 20
                                else:
                                    score -= (9 - row) * 10
        
        # Add checkmate potential evaluation - adjusted for color
        checkmate_score = (self.evaluate_checkmate_potential(color) - 
                          self.evaluate_checkmate_potential('red' if color == 'black' else 'black'))
        score += checkmate_score * 2  # Give high weight to checkmate potential
        
        # King safety evaluation - adjusted for color
        king_safety = (self.evaluate_king_safety(color) - 
                      self.evaluate_king_safety('red' if color == 'black' else 'black'))
        score += king_safety
        
        return score





    # YELLOW HIGHTLIGHT(2nd modification)

    def highlight_piece(self, row, col):
        """Draw a yellow highlight around the selected piece"""
        # Calculate position on intersections
        x = self.board_margin + col * self.cell_size
        y = self.board_margin + row * self.cell_size
        
        # Create a yellow square around the piece
        self.canvas.create_rectangle(
            x - self.piece_radius - 2,
            y - self.piece_radius - 2,
            x + self.piece_radius + 2,
            y + self.piece_radius + 2,
            outline='yellow',
            width=2,
            tags='highlight'
        )    


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

    def get_piece_position_descriptor(self, from_pos, to_pos, piece):
        """
        Determine 前/后 based on proximity to opponent's king.
        If the piece is closer to the opponent's king, it's labeled '前',
        otherwise it's labeled '后'.
        """
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        piece_color = piece[0]  # 'R' for red or 'B' for black
        piece_type = piece[1]   # The type of piece (炮, 車, etc.)
        
        # Find all identical pieces in the same column
        identical_positions = []
        for row in range(10):
            current_piece = self.board[row][from_col]
            if current_piece:

                if piece_type == '馬' and current_piece[0] == piece_color and current_piece[1] == piece_type:
                    identical_positions.append(row)
                else:


                    if current_piece[0] == piece_color and current_piece[1] == piece_type and row != to_row:
                        identical_positions.append(row)
        identical_positions.append(from_row)
                
        # If there are two identical pieces in the same column
        if len(identical_positions) == 2:
            # Find opponent's king position
            red_king_pos, black_king_pos = self.find_kings()
            opponent_king_row = black_king_pos[0] if piece_color == 'R' else red_king_pos[0]
            
            # Calculate distances to opponent's king for both pieces
            distances = [(abs(row - opponent_king_row), row) for row in identical_positions]
            
            # The piece closer to opponent's king is '前', the other is '后'
            distances.sort()  # Sort by distance to opponent's king
            if from_row == distances[0][1]:  # If this is the closer piece
                return "前"
            else:
                return "后"
        
        # Return empty string if there's only one piece of this type in the column
        return ""

    def get_move_text(self, from_pos, to_pos, piece):
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
        position_descriptor = self.get_piece_position_descriptor(from_pos, to_pos, piece)
        
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
                self.move_text.insert(tk.END, f"{i}. {move}\n")
            self.move_text.config(state='disabled')
            self.move_text.see(tk.END)  # Scroll to the bottom

    def toggle_records(self):
        """Toggle the visibility of the records frame"""
        self.records_seen = not self.records_seen
        self.records_button.destroy()
        
        self.records_button = ttk.Button(
            self.button_frame,
            text="棋谱记录",
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



    # Add this new method to the ChineseChess class
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

    # Modify the next_replay_move method to include the highlighting
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

    # Also modify the prev_replay_move method to update the highlighting
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
        
        if self.current_replay_index > 1:

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
            self.initialize_board()
        
        # Update highlights if not at the beginning
        if self.current_replay_index > 0:
            move = self.move_history[self.current_replay_index - 1]
            self.highlighted_positions = [move['from_pos'], move['to_pos']]
        else:
            self.highlighted_positions = []
        
        self.draw_board()

    # Modify the start_replay method to clear any existing highlights
    def start_replay(self):
        """Start replay mode"""
        self.switch_color_button.config(state=tk.DISABLED)

        if not self.move_history:
            self.show_centered_warning("提示", "没有可以回放的历史记录")
            return
            
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

        # Draw column numbers at top and bottom
        # List of Chinese numbers for red side
        red_numbers = ['九', '八', '七', '六', '五', '四', '三', '二', '一']
        red_numbers_flipped = ['一', '二', '三', '四', '五', '六', '七', '八', '九']    

        # List of Arabic numbers for black side
        black_numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
        black_numbers_flipped = ['9', '8', '7', '6', '5', '4', '3', '2', '1']   

        # Draw top numbers
        top_numbers = black_numbers if not self.flipped else red_numbers_flipped
        for col, num in enumerate(top_numbers):
            x = self.board_margin + col * self.cell_size
            y = self.board_margin - 37
            self.canvas.create_text(
                x, y,
                text=num,
                fill='black',
                font=('Arial', 12)
            )

        # Draw bottom numbers
        bottom_numbers = red_numbers if not self.flipped else black_numbers_flipped
        for col, num in enumerate(bottom_numbers):
            x = self.board_margin + col * self.cell_size
            y = self.canvas_height - self.board_margin + 37
            self.canvas.create_text(
                x, y,
                text=num,
                fill='black',
                font=('Arial', 12)
            )

    def restart_game(self):
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

    # the following 3 functions (conbined with on_click function) is to add the CHECK feature
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