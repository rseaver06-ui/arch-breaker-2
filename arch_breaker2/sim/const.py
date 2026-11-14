"""Fixed playfield numbers. The window scales this 640x360 canvas by whole pixels."""

TICK = 1.0 / 60.0
W, H = 640, 360
HUD_H = 36
COURT_L, COURT_T, COURT_R, COURT_B = 8, 40, 632, 352

COLS, MAX_ROWS = 14, 8
BRICK_W, BRICK_H, GAP_X, GAP_Y = 42, 12, 2, 3
GRID_L = (W - (COLS * BRICK_W + (COLS - 1) * GAP_X)) // 2
GRID_T = 56

PADDLE_W, PADDLE_H, PADDLE_Y = 72, 6, 330
WIDE_W = 120
PADDLE_MAX = 420.0
PADDLE_ACCEL_T = 0.06
PADDLE_DECEL_T = 0.08
SPIN = 0.22          # how much paddle motion bends the ball
EDGE_FRAC = 0.85     # outer 15% of the paddle counts as an edge save

BALL_R = 3
BALL_BASE = 190.0
BALL_PER_HIT = 6.0
MIN_VY = 0.34        # ball never goes flatter than this
MAX_SIN = 0.866      # 60 degrees off vertical at the paddle's edge
LIVES = 3
MAX_BALLS = 6

DROP_SIZE = 10
DROP_SPEED = 90.0
WIDE_T, PASS_T, SLOW_T = 12.0, 8.0, 8.0
SLOW_SCALE = 0.65
KINDS = ("wide", "shield", "multi", "pass", "slow")

LAST_BRICK_T = 20.0
HELP_WINDOW = 20.0   # seconds after a lost ball when drops lean helpful
HOT_STREAK = 30      # paddle hits without a loss: drops lean risky
CREEP_LEVEL = 8
CREEP_HITS = 12
CLEAR_BONUS = 100
PENALTY = 25          # versus: a ball through your side
RESPAWN_TICKS = 60


def speed_cap(level: int) -> float:
    return min(440.0, 300.0 + 12.0 * level)
