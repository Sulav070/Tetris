# --- IMPORTS & INIT ---
import pygame
import random
import json

pygame.init()

# --- CONSTANTS & COLORS ---
COLS, ROWS = 12, 20
BLOCK_SIZE = 30
RIGHT_PANEL_WIDTH = 320
WIDTH = COLS * BLOCK_SIZE + RIGHT_PANEL_WIDTH + 20
HEIGHT = ROWS * BLOCK_SIZE + 40

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 150, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (30, 30, 30)
RED = (255, 0, 0)

COLORS = [
    (0, 255, 255), (0, 0, 255), (255, 127, 0),
    (255, 255, 0), (0, 255, 0), (160, 32, 240),
    (255, 0, 0)
]

FONT = pygame.font.SysFont("Arial", 24)
MID_FONT = pygame.font.SysFont("Arial", 36, bold=True)
COUNTDOWN_FONT = pygame.font.SysFont("Arial", 56, bold=True)
THIN_FONT = pygame.font.SysFont("Courier", 28)

SHAPES = {
    'I': [[1,1,1,1]],
    'O': [[1,1],[1,1]],
    'T': [[0,1,0],[1,1,1]],
    'S': [[0,1,1],[1,1,0]],
    'Z': [[1,1,0],[0,1,1]],
    'J': [[1,0,0],[1,1,1]],
    'L': [[0,0,1],[1,1,1]]
}

GRID_OFFSET_X = 10
GRID_OFFSET_Y = HEIGHT - (ROWS * BLOCK_SIZE) - 10
RIGHT_X = WIDTH - RIGHT_PANEL_WIDTH + 40

# --- HELPER FUNCTIONS ---
def center_in_right_panel(item_width):
    return RIGHT_X + (RIGHT_PANEL_WIDTH - 40 - item_width) // 2

def create_grid(locked_positions):
    grid = [[BLACK for _ in range(COLS)] for _ in range(ROWS)]
    for (x, y), color in locked_positions.items():
        if 0 <= y < ROWS and 0 <= x < COLS:
            grid[y][x] = color
    return grid

def valid(piece, grid, dx=0, dy=0):
    for r, row in enumerate(piece.shape):
        for c, cell in enumerate(row):
            if cell:
                nx, ny = piece.x + c + dx, piece.y + r + dy
                if nx < 0 or nx >= COLS or ny >= ROWS or (ny >= 0 and grid[ny][nx] != BLACK):
                    return False
    return True

def lock_piece(piece, locked_positions):
    for r, row in enumerate(piece.shape):
        for c, cell in enumerate(row):
            if cell:
                locked_positions[(piece.x + c, piece.y + r)] = piece.color

def check_full_rows(grid):
    return [i for i, row in enumerate(grid) if BLACK not in row]

def clear_rows(locked_positions, full_rows):
    for row in sorted(full_rows):
        for x in range(COLS):
            locked_positions.pop((x, row), None)
    shift = 0
    for row in reversed(range(ROWS)):
        if row in full_rows:
            shift += 1
        elif shift > 0:
            for x in range(COLS):
                if (x, row) in locked_positions:
                    locked_positions[(x, row + shift)] = locked_positions.pop((x, row))

def draw_grid(screen, grid):
    for r in range(ROWS):
        for c in range(COLS):
            x = GRID_OFFSET_X + c * BLOCK_SIZE
            y = GRID_OFFSET_Y + r * BLOCK_SIZE
            pygame.draw.rect(screen, grid[r][c], (x, y, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(screen, DARK_GRAY, (x, y, BLOCK_SIZE, BLOCK_SIZE), 1)

def draw_piece(screen, piece, offset_x, offset_y):
    for r, row in enumerate(piece.shape):
        for c, cell in enumerate(row):
            if cell:
                x = offset_x + c * BLOCK_SIZE
                y = offset_y + r * BLOCK_SIZE
                pygame.draw.rect(screen, piece.color, (x, y, BLOCK_SIZE, BLOCK_SIZE))
                pygame.draw.rect(screen, DARK_GRAY, (x, y, BLOCK_SIZE, BLOCK_SIZE), 1)

def draw_hold_piece(screen, hold, x, y):
    if hold:
        draw_piece(screen, hold, x, y)

def draw_counter(screen, label, value, x, y, color=GREEN):
    vs = str(min(value, 99999)).rjust(5, '0')
    width = 220
    box_x = x - 50
    pygame.draw.rect(screen, BLACK, (box_x, y - 5, width, 50))
    pygame.draw.rect(screen, color, (box_x, y - 5, width, 50), 2)
    label_surface = FONT.render(label, True, color)
    value_surface = THIN_FONT.render(vs, True, color)
    screen.blit(label_surface, (x - 10, y))
    screen.blit(value_surface, (x + 150 - value_surface.get_width() - 10, y))

def draw_controls(screen, x, y):
    lines = ["Controls:", "↑/W Rotate", "←/A Left", "→/D Right", "↓/S Drop", "Space Hard Drop", "C Hold", "P Pause"]
    for i, line in enumerate(lines):
        screen.blit(FONT.render(line, True, BLUE), (x, y + i * 24))

def save_highscore(score):
    try:
        with open("score.json", "r+") as f:
            data = json.load(f)
            if score > data.get("highscore", 0):
                f.seek(0)
                json.dump({"highscore": score}, f)
                f.truncate()
    except:
        with open("score.json", "w") as f:
            json.dump({"highscore": score}, f)

def load_highscore():
    try:
        with open("score.json", "r") as f:
            return json.load(f).get("highscore", 0)
    except:
        return 0

# --- PIECE CLASS ---
class Piece:
    def __init__(self, shape_key):
        self.shape = SHAPES[shape_key]
        self.color = COLORS[list(SHAPES).index(shape_key)]
        self.x = COLS // 2 - len(self.shape[0]) // 2
        self.y = 0
        self.type = shape_key

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

# --- GAME OVER SCREEN ---
def game_over_screen(screen, score, highscore):
    start_time = pygame.time.get_ticks()
    timeout = 10
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    return False
                if event.key == pygame.K_r:
                    return True

        elapsed = (pygame.time.get_ticks() - start_time) // 1000
        remaining = timeout - elapsed
        if remaining < 0:
            return False

        screen.fill(BLACK)

        # GAME OVER - Red
        go_text = COUNTDOWN_FONT.render("GAME OVER", True, RED)
        screen.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, 130))

        # Score + High Score - Large Green
        score_text = MID_FONT.render(f"Score: {score}", True, GREEN)
        high_text = MID_FONT.render(f"High: {highscore}", True, GREEN)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 220))
        screen.blit(high_text, (WIDTH // 2 - high_text.get_width() // 2, 270))

        # Exiting in X - Small Red
        exit_text = FONT.render(f"Exiting in {remaining}", True, RED)
        screen.blit(exit_text, (WIDTH // 2 - exit_text.get_width() // 2, 320))

        # Prompt: Press E to Exit or R for Rematch
        prompt = "Press "
        p1 = FONT.render(prompt, True, WHITE)
        e = FONT.render("E", True, BLUE)
        p2 = FONT.render(" to Exit or Press ", True, WHITE)
        r = FONT.render("R", True, BLUE)
        p3 = FONT.render(" for Rematch", True, WHITE)
        x = WIDTH // 2 - (p1.get_width() + e.get_width() + p2.get_width() + r.get_width() + p3.get_width()) // 2
        screen.blit(p1, (x, 370)); x += p1.get_width()
        screen.blit(e, (x, 370)); x += e.get_width()
        screen.blit(p2, (x, 370)); x += p2.get_width()
        screen.blit(r, (x, 370)); x += r.get_width()
        screen.blit(p3, (x, 370))

        pygame.display.update()
        pygame.time.delay(100)

# --- MAIN GAME LOOP ---
def game_loop():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()

    locked_positions = {}
    grid = create_grid(locked_positions)

    def bagf():
        b = list(SHAPES) * 4
        random.shuffle(b)
        return b

    bag = bagf()
    def nxt():
        nonlocal bag
        if len(bag) < 2:
            bag += bagf()
        return Piece(bag.pop())

    current = nxt()
    next_piece = nxt()
    hold_piece = None
    can_hold = True

    fall_time = 0
    fall_speed = 500
    paused = False
    score = 0
    highscore = load_highscore()
    MOVE_DELAY = 120
    last_move = pygame.time.get_ticks()

    while True:
        dt = clock.tick()
        if not paused:
            fall_time += dt
        if not paused and fall_time > fall_speed:
            fall_time = 0
            if valid(current, grid, dy=1):
                current.y += 1
            else:
                lock_piece(current, locked_positions)
                grid = create_grid(locked_positions)
                full_rows = check_full_rows(grid)
                if full_rows:
                    for _ in range(3):
                        for row in full_rows:
                            for x in range(COLS):
                                grid[row][x] = WHITE
                        draw_grid(screen, grid)
                        pygame.display.update()
                        pygame.time.delay(80)
                        for row in full_rows:
                            for x in range(COLS):
                                grid[row][x] = BLACK
                        draw_grid(screen, grid)
                        pygame.display.update()
                        pygame.time.delay(80)
                    clear_rows(locked_positions, full_rows)
                    grid = create_grid(locked_positions)
                    score += len(full_rows) * 100
                current = next_piece
                next_piece = nxt()
                can_hold = True
                if not valid(current, grid):
                    save_highscore(score)
                    if game_over_screen(screen, score, highscore):
                        locked_positions.clear()
                        grid = create_grid(locked_positions)
                        bag = bagf()
                        current = nxt()
                        next_piece = nxt()
                        hold_piece = None
                        can_hold = True
                        fall_time = 0
                        score = 0
                        highscore = load_highscore()
                        paused = False
                        continue
                    else:
                        return False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    current.rotate()
                    if not valid(current, grid):
                        for _ in range(3): current.rotate()
                elif event.key == pygame.K_c and can_hold:
                    if hold_piece is None:
                        hold_piece = Piece(current.type)
                        current = next_piece
                        next_piece = nxt()
                    else:
                        hold_piece, current = Piece(current.type), Piece(hold_piece.type)
                        current.x = COLS // 2 - len(current.shape[0]) // 2
                        current.y = 0
                    can_hold = False
                elif event.key == pygame.K_SPACE:
                    while valid(current, grid, dy=1):
                        current.y += 1
                elif event.key == pygame.K_p:
                    paused = not paused

        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()
        if not paused and now - last_move > MOVE_DELAY:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                if valid(current, grid, dx=-1):
                    current.x -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if valid(current, grid, dx=1):
                    current.x += 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                if valid(current, grid, dy=1):
                    current.y += 1
            last_move = now

        screen.fill(DARK_GRAY)
        grid = create_grid(locked_positions)
        draw_grid(screen, grid)

        draw_piece(screen, current, GRID_OFFSET_X + current.x * BLOCK_SIZE, GRID_OFFSET_Y + current.y * BLOCK_SIZE)

        next_piece_x = center_in_right_panel(BLOCK_SIZE * len(next_piece.shape[0]))
        screen.blit(FONT.render("Next", True, WHITE), (center_in_right_panel(FONT.size("Next")[0]), 30))
        draw_piece(screen, next_piece, next_piece_x, 60)

        hold_piece_x = center_in_right_panel(BLOCK_SIZE * 4)
        screen.blit(FONT.render("Hold", True, WHITE), (center_in_right_panel(FONT.size("Hold")[0]), 150))
        draw_hold_piece(screen, hold_piece, hold_piece_x, 180)

        draw_controls(screen, RIGHT_X + 20, 280)
        draw_counter(screen, "Score", score, center_in_right_panel(150), HEIGHT - 120)
        draw_counter(screen, "High", highscore, center_in_right_panel(150), HEIGHT - 60)

        if paused:
            screen.blit(FONT.render("PAUSED", True, WHITE), (WIDTH // 2 - 60, HEIGHT // 2))

        pygame.display.update()

# --- MAIN ---
def main():
    while True:
        if not game_loop():
            break
    pygame.quit()

if __name__ == "__main__":
    main()
