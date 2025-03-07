import pygame
from pygame.locals import *

pygame.init()

WINDOW_WIDTH = 1500
WINDOW_HEIGHT = 1000
CELL_SIZE = 200
MARGIN_X = (WINDOW_WIDTH - 3 * CELL_SIZE) // 2
MARGIN_Y = (WINDOW_HEIGHT - 3 * CELL_SIZE) // 2
SIZE_VALUES = {'large': 80, 'medium': 50, 'small': 30}

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
LIGHT_RED = (255, 150, 150)
BUTTON_RED = (220, 50, 50)

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        font = pygame.font.Font(None, 36)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Piece:
    def __init__(self, color, size):
        self.color = color
        self.size = size

class GameState:
    def __init__(self):
        self.board = [[[] for _ in range(3)] for _ in range(3)]
        self.reserves = {
            'red': {'large': 2, 'medium': 2, 'small': 2},
            'yellow': {'large': 2, 'medium': 2, 'small': 2}
        }
        self.current_player = 'red'
        self.selected_size = None
        self.dragging_piece = None
        self.source_cell = None
        self.touched_piece = None
        self.touched_location = None
        self.must_move_touched = False
        self.forfeit_button = Button(
            WINDOW_WIDTH - 200, WINDOW_HEIGHT - 200, 
            180, 60, "Forfeit", BUTTON_RED, LIGHT_RED
        )

    def get_opponent(self):
        return 'yellow' if self.current_player == 'red' else 'red'

    def check_win(self, color):
        lines = [
            [(0,0), (0,1), (0,2)], [(1,0), (1,1), (1,2)], [(2,0), (2,1), (2,2)],
            [(0,0), (1,0), (2,0)], [(0,1), (1,1), (2,1)], [(0,2), (1,2), (2,2)],
            [(0,0), (1,1), (2,2)], [(0,2), (1,1), (2,0)]
        ]
        for line in lines:
            if all(self.board[r][c] and self.board[r][c][-1].color == color for (r, c) in line):
                return True
        return False

    def can_place(self, size, row, col):
        if not (0 <= row < 3 and 0 <= col < 3):
            return False
        cell = self.board[row][col]
        return not cell or SIZE_VALUES[size] > SIZE_VALUES[cell[-1].size]

    def place_piece(self, size, row, col):
        if self.reserves[self.current_player][size] <= 0:
            return False
        if not self.can_place(size, row, col):
            return False
        self.board[row][col].append(Piece(self.current_player, size))
        self.reserves[self.current_player][size] -= 1
        return True

    def can_move(self, src_row, src_col, dest_row, dest_col):
        if not (0 <= src_row < 3 and 0 <= src_col < 3):
            return False
        src = self.board[src_row][src_col]
        if not src or src[-1].color != self.current_player:
            return False
        if (src_row, src_col) == (dest_row, dest_col):
            return False
        dest = self.board[dest_row][dest_col]
        return not dest or SIZE_VALUES[src[-1].size] > SIZE_VALUES[dest[-1].size]

    def move_piece(self, src_row, src_col, dest_row, dest_col):
        if not self.can_move(src_row, src_col, dest_row, dest_col):
            return False
        
        piece = self.board[src_row][src_col].pop()
        
        opponent = self.get_opponent()
        exposed_win = self.check_win(opponent)
        
        if exposed_win:
            lines = [
                [(0,0), (0,1), (0,2)], [(1,0), (1,1), (1,2)], [(2,0), (2,1), (2,2)],
                [(0,0), (1,0), (2,0)], [(0,1), (1,1), (2,1)], [(0,2), (1,2), (2,2)],
                [(0,0), (1,1), (2,2)], [(0,2), (1,1), (2,0)]
            ]
            winning_positions = []
            for line in lines:
                if all(self.board[r][c] and self.board[r][c][-1].color == opponent for (r, c) in line):
                    winning_positions.extend(line)
            
            self.board[src_row][src_col].append(piece)
           
            if (dest_row, dest_col) not in winning_positions:
                self.board[src_row][src_col].pop()
                self.board[dest_row][dest_col].append(piece)
                return "opponent_win"
            
            self.board[src_row][src_col].pop()
        
        self.board[dest_row][dest_col].append(piece)
        return True

    def has_valid_moves(self):
        if not self.touched_location:
            return False
            
        src_row, src_col = self.touched_location
        for dest_row in range(3):
            for dest_col in range(3):
                if self.can_move(src_row, src_col, dest_row, dest_col):
                    return True
        return False

    def reset_touched(self):
        self.touched_piece = None
        self.touched_location = None
        self.must_move_touched = False
        
    def forfeit(self):
        return self.get_opponent()

def draw_board(screen, game_state):
    screen.fill(WHITE)
    for row in range(3):
        for col in range(3):
            x = MARGIN_X + col * CELL_SIZE
            y = MARGIN_Y + row * CELL_SIZE
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 3)
            stack = game_state.board[row][col]
            if stack:
                piece = stack[-1]
                color = RED if piece.color == 'red' else YELLOW
                radius = SIZE_VALUES[piece.size]
                pygame.draw.circle(screen, color, (x + CELL_SIZE//2, y + CELL_SIZE//2), radius)
                
                if game_state.touched_piece and game_state.touched_location == (row, col):
                    glow_color = (255, 165, 0)   
                    pygame.draw.circle(screen, glow_color, (x + CELL_SIZE//2, y + CELL_SIZE//2), radius + 5, 3)
    
    for size_idx, size in enumerate(['large', 'medium', 'small']):
        count = game_state.reserves['red'][size]
        for i in range(count):
            x = 100 + (size_idx * 200) 
            y = 100 + (i * 100) 
            pygame.draw.circle(screen, RED, (x, y), SIZE_VALUES[size])
            pygame.draw.circle(screen, BLACK, (x, y), SIZE_VALUES[size], 2)
    
    for size_idx, size in enumerate(['large', 'medium', 'small']):
        count = game_state.reserves['yellow'][size]
        for i in range(count):
            x = WINDOW_WIDTH - 100 - (size_idx * 200) 
            y = 100 + (i * 100)  
            pygame.draw.circle(screen, YELLOW, (x, y), SIZE_VALUES[size])
            pygame.draw.circle(screen, BLACK, (x, y), SIZE_VALUES[size], 2)

    font = pygame.font.Font(None, 36)
    text = font.render(f"Current Player: {game_state.current_player}", True, BLACK)
    screen.blit(text, (10, 10))
    
    if game_state.selected_size:
        text = font.render(f"Selected: {game_state.selected_size}", True, BLACK)
        screen.blit(text, (10, 50))
    
    if game_state.must_move_touched:
        if game_state.has_valid_moves():
            text = font.render(f"You must move the highlighted piece!", True, RED)
        else:
            text = font.render(f"No valid moves! Click Forfeit to continue.", True, RED)
        screen.blit(text, (WINDOW_WIDTH//2 - 200, 50))
        
        game_state.forfeit_button.draw(screen)
    
    if game_state.dragging_piece:
        x, y = pygame.mouse.get_pos()
        color = RED if game_state.dragging_piece.color == 'red' else YELLOW
        radius = SIZE_VALUES[game_state.dragging_piece.size]
        pygame.draw.circle(screen, color, (x, y), radius)
        pygame.draw.circle(screen, BLACK, (x, y), radius, 2)
    
    pygame.display.flip()

def show_winner(screen, game_state, winner, reason=""):
    draw_board(screen, game_state)
    
    pygame.time.wait(1000)

    font = pygame.font.Font(None, 74)
    text = font.render(f"{winner} wins!", True, BLACK)
    text_rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
    screen.blit(text, text_rect)
    
    if reason:
        reason_font = pygame.font.Font(None, 48)
        reason_text = reason_font.render(reason, True, BLACK)
        reason_rect = reason_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 80))
        screen.blit(reason_text, reason_rect)
    
    pygame.display.flip()
    pygame.time.wait(3000)

def main():
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Gobblet Jr.")
    
    game_state = GameState()
    running = True
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        if game_state.must_move_touched:
            game_state.forfeit_button.check_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == MOUSEBUTTONDOWN:
                x, y = event.pos
                
                if game_state.must_move_touched and game_state.forfeit_button.is_clicked((x, y)):
                    winner = game_state.forfeit()
                    show_winner(screen, game_state, winner, "by forfeit")
                    running = False
                    continue
                
                if game_state.must_move_touched:
                    row, col = game_state.touched_location
                    board_x = MARGIN_X + col * CELL_SIZE + CELL_SIZE//2
                    board_y = MARGIN_Y + row * CELL_SIZE + CELL_SIZE//2
                    piece = game_state.board[row][col][-1]
                    radius = SIZE_VALUES[piece.size]
                    
                    if (x - board_x)**2 + (y - board_y)**2 <= radius**2:
                        game_state.dragging_piece = piece
                        game_state.source_cell = (row, col)
                    continue
                
                red_clicked = False
                for size_idx, size in enumerate(['large', 'medium', 'small']):
                    for i in range(game_state.reserves['red'][size]):
                        rx = 100 + (size_idx * 200)
                        ry = 100 + (i * 100)
                        if (x - rx)**2 + (y - ry)**2 <= SIZE_VALUES[size]**2:
                            if game_state.current_player == 'red':
                                game_state.selected_size = size
                                red_clicked = True
                                break
                    if red_clicked:
                        break
                
                yellow_clicked = False
                if not red_clicked:
                    for size_idx, size in enumerate(['large', 'medium', 'small']):
                        for i in range(game_state.reserves['yellow'][size]):
                            yx = WINDOW_WIDTH - 100 - (size_idx * 200)
                            yy = 100 + (i * 100)
                            
                            if (x - yx)**2 + (y - yy)**2 <= SIZE_VALUES[size]**2:
                                if game_state.current_player == 'yellow':
                                    game_state.selected_size = size
                                    yellow_clicked = True
                                    break
                        if yellow_clicked:
                            break
                
                if not (red_clicked or yellow_clicked):
                    col = (x - MARGIN_X) // CELL_SIZE
                    row = (y - MARGIN_Y) // CELL_SIZE
                    if 0 <= row < 3 and 0 <= col < 3:
                        if game_state.selected_size is not None:
                            if game_state.place_piece(game_state.selected_size, row, col):
                                opponent = game_state.get_opponent()
                                if game_state.check_win(opponent):
                                    show_winner(screen, game_state, opponent)
                                    running = False
                                elif game_state.check_win(game_state.current_player):
                                    show_winner(screen, game_state, game_state.current_player)
                                    running = False
                                else:
                                    game_state.current_player = opponent
                                game_state.selected_size = None
                                game_state.reset_touched()
                        else:
                            if game_state.board[row][col] and game_state.board[row][col][-1].color == game_state.current_player:
                                game_state.touched_piece = game_state.board[row][col][-1]
                                game_state.touched_location = (row, col)
                                game_state.must_move_touched = True
                                
                                game_state.dragging_piece = game_state.touched_piece
                                game_state.source_cell = (row, col)
                            
            elif event.type == MOUSEBUTTONUP and game_state.dragging_piece:
                x, y = event.pos
                dest_col = (x - MARGIN_X) // CELL_SIZE
                dest_row = (y - MARGIN_Y) // CELL_SIZE
                if 0 <= dest_row < 3 and 0 <= dest_col < 3:
                    src_row, src_col = game_state.source_cell
                    move_result = game_state.move_piece(src_row, src_col, dest_row, dest_col)
                    
                    if move_result == "opponent_win":
                        opponent = game_state.get_opponent()
                        show_winner(screen, game_state, opponent)
                        running = False
                    elif move_result:
                        opponent = game_state.get_opponent()
                        if game_state.check_win(opponent):
                            show_winner(screen, game_state, opponent)
                            running = False
                        elif game_state.check_win(game_state.current_player):
                            show_winner(screen, game_state, game_state.current_player)
                            running = False
                        else:
                            game_state.current_player = opponent
                            game_state.reset_touched()
                    else:
                        game_state.must_move_touched = True
                
                game_state.dragging_piece = None
                game_state.source_cell = None
        
        draw_board(screen, game_state)
    
    pygame.quit()

if __name__ == "__main__":
    main()