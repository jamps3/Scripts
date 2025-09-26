import math, random, sys, time, argparse, platform

# OS detection
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import msvcrt
else:
    import termios, tty, select

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("width", type=int, nargs="?", default=360, help="Width in characters")
parser.add_argument("height", type=int, nargs="?", default=92, help="Height in characters")
parser.add_argument("fps", type=int, nargs="?", default=60, help="Frames per second")
parser.add_argument("frames", type=int, nargs="?", default=10000, help="Total frames to display")
parser.add_argument("palette", type=int, nargs="?", default=0, help="Palette index (1–8)")
parser.add_argument("change_count", type=int, nargs="?", default=1, help="Number of parameters to change simultaneously")
parser.add_argument("change_amount", type=float, nargs="?", default=0.05, help="Amount to change parameters by")
args = parser.parse_args()

WIDTH, HEIGHT = args.width, args.height
FPS, FRAMES = args.fps, args.frames
CHANGE_COUNT, CHANGE_AMOUNT = args.change_count, args.change_amount
DELAY = 1.0 / FPS

# Terminal setup
if not IS_WINDOWS:
    original_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
sys.stdout.write("\033[?25l\033[2J")  # Hide cursor, clear screen
sys.stdout.flush()

def get_key():
    if IS_WINDOWS:
        return msvcrt.getwch() if msvcrt.kbhit() else None
    else:
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        return sys.stdin.read(1) if dr else None

def show_controls():
    controls = [
        "🎮 Controls:",
        "  w/s → freq_r ±",
        "  a/d → freq_a ±",
        "  i/k → phase_a ±",
        "  j/l → phase_r ±",
        "  p   → next palette",
        "  q   → quit",
        ""
    ]
    for i, line in enumerate(controls):
        sys.stdout.write(f"\033[{i+1};1H\033[0m{line}")
    sys.stdout.flush()

def show_controls_inline():
    sys.stdout.write("\033[1;1H\033[2K\033[0m")  # Clear line 1
    sys.stdout.write(
        "🎮 w/s=freq_r a/d=freq_a i/k=phase_a j/l=phase_r p=next_palette 1–8=select_palette h=help q=quit"
    )
    sys.stdout.flush()

class MandalaParams:
    def __init__(self, palette_index=0):
        self.freq_r = random.uniform(0.1, 1.5)
        self.freq_a = random.uniform(1.0, 6.0)
        self.phase_r = random.uniform(0, math.pi * 2)
        self.phase_a = random.uniform(0, math.pi * 2)
        self.offset_x = random.randint(-5, 5)
        self.offset_y = random.randint(-5, 5)
        self.palettes = [  # 8 different character palettes
            [' ', '.', '*', '+', 'x', 'X', 'o', 'O', '@', '#'],
            [' ', '-', '=', '~', '^', '*', '%', '$', '&', '#'],
            [' ', '.', ':', ';', '!', '?', '/', '|', '\\', '#'],
            [' ', '·', '•', '*', '¤', '°', '○', '●', '◎', '■'],
            [' ', '˙', '⁕', '✦', '✧', '✶', '✷', '✸', '✺', '✹'],
            [' ', '·', '•', '◦', '○', '◉', '◎', '◍', '◯', '⬤'],
            [' ', '░', '▒', '▓', '▙', '▛', '▜', '▟', '█', '🟥'],
            [' ', '⎯', '⎼', '⎻', '﹏', '╌', '╍', '╏', '╎', '╳']
        ]
        self.palette_index = max(0, min(palette_index, len(self.palettes) - 1))
        self.transition_frames = 0
        self.target_palette_index = self.palette_index

    @property
    def palette(self):
        return self.get_blended_palette()

    def mutate(self, key):
        if key == 'q': return 'quit', None
        if key == 'w': self.freq_r += CHANGE_AMOUNT; return 'freq_r', +1
        if key == 's': self.freq_r -= CHANGE_AMOUNT; return 'freq_r', -1
        if key == 'a': self.freq_a -= CHANGE_AMOUNT * 2; return 'freq_a', -1
        if key == 'd': self.freq_a += CHANGE_AMOUNT * 2; return 'freq_a', +1
        if key == 'j': self.phase_r += CHANGE_AMOUNT * 3; return 'phase_r', +1
        if key == 'l': self.phase_r -= CHANGE_AMOUNT * 3; return 'phase_r', -1
        if key == 'i': self.phase_a += CHANGE_AMOUNT * 3; return 'phase_a', +1
        if key == 'k': self.phase_a -= CHANGE_AMOUNT * 3; return 'phase_a', -1
        if key == 'p': self.palette_index = (self.palette_index + 1) % len(self.palettes); return 'palette', +1
        if key in '12345678':
            self.target_palette_index = int(key) - 1
            self.transition_frames = 30  # Palette transition over 30 frames
            return 'palette', 0
        if key == 'h':
            return 'help', None
        return None, None

    def get_blended_palette(self):
        if self.transition_frames == 0:
            return self.palettes[self.palette_index]
        src = self.palettes[self.palette_index]
        tgt = self.palettes[self.target_palette_index]
        blend = []
        for a, b in zip(src, tgt):
            blend.append(b if self.transition_frames < 10 else a)
        self.transition_frames -= 1
        if self.transition_frames == 0:
            self.palette_index = self.target_palette_index
        return blend

def generate_frame(params, frame_count):
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    hue_shift = frame_count * 2
    frame = [[' '] * WIDTH for _ in range(HEIGHT)]
    color = [[(255,255,255)] * WIDTH for _ in range(HEIGHT)]

    for y in range(HEIGHT):
        for x in range(WIDTH):
            dx = x - center_x + params.offset_x
            dy = y - center_y + params.offset_y
            r = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)
            val = math.sin(r * params.freq_r + params.phase_r) + math.cos(angle * params.freq_a + params.phase_a)
            index = int((val + 2) / 4 * len(params.palette))
            frame[y][x] = params.palette[index % len(params.palette)]

            hue = int((r / (WIDTH / 2)) * 255 + hue_shift) % 256
            red   = int((math.sin(hue * 0.03) + 1) * 127)
            green = int((math.sin(hue * 0.05 + 2) + 1) * 127)
            blue  = int((math.sin(hue * 0.07 + 4) + 1) * 127)
            color[y][x] = (red, green, blue)
    return frame, color

def render_frame(prev, curr, colors):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if curr[y][x] != prev[y][x]:
                r, g, b = colors[y][x]
                sys.stdout.write(f"\033[{y+2};{x+1}H\033[38;2;{r};{g};{b}m{curr[y][x]}")
                prev[y][x] = curr[y][x]
    sys.stdout.write("\033[0m")
    sys.stdout.flush()

def display_settings(params, active_param):
    sys.stdout.write(f"\033[{HEIGHT+2};1H\033[0m")
    sys.stdout.write(
        f"🎛 freq_r={params.freq_r:.2f} freq_a={params.freq_a:.2f} "
        f"phase_r={params.phase_r:.2f} phase_a={params.phase_a:.2f} "
        f"offset_x={params.offset_x} offset_y={params.offset_y} "
        f"palette={params.palette_index + 1}/{len(params.palettes)} "
        f"→ animating: {active_param or 'none'}"
    )
    palette_preview = ''.join(params.palette)
    sys.stdout.write(f"\n🧵 Palette: {palette_preview}")
    sys.stdout.flush()

def main():
    show_controls_inline()
    params = MandalaParams(palette_index=args.palette - 1)
    prev_frame = [[' '] * WIDTH for _ in range(HEIGHT)]
    active_param = None
    active_direction = +1
    frame_count = 0

    try:
        for _ in range(FRAMES):
            key = get_key()
            if key:
                param, direction = params.mutate(key)
                if param == 'quit':
                    break
                elif param == 'help':
                    show_controls_inline()
                elif param:
                    if param != 'palette':  # prevent palette from being animated
                        active_param = param
                        active_direction = direction

            # Animate active parameter
            delta = CHANGE_AMOUNT * active_direction
            if active_param == 'freq_r': params.freq_r += delta
            elif active_param == 'freq_a': params.freq_a += delta * 2
            elif active_param == 'phase_r': params.phase_r += delta * 3
            elif active_param == 'phase_a': params.phase_a += delta * 3
            elif active_param == 'offset_x': params.offset_x += int(delta * 10)
            elif active_param == 'offset_y': params.offset_y += int(delta * 10)

            curr_frame, colors = generate_frame(params, frame_count)
            render_frame(prev_frame, curr_frame, colors)
            display_settings(params, active_param)
            time.sleep(DELAY)
            frame_count += 1
    except KeyboardInterrupt:
        pass
    finally:
        if not IS_WINDOWS:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_settings)
        sys.stdout.write("\033[?25h\033[0m\n")  # Show cursor, reset
        sys.stdout.flush()

main()