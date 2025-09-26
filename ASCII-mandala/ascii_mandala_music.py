import math, random, sys, time, argparse, platform
import numpy as np
import sounddevice as sd

# OS detection
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import msvcrt
else:
    import termios, tty, select

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("width", type=int, nargs="?", default=360)
parser.add_argument("height", type=int, nargs="?", default=92)
parser.add_argument("fps", type=int, nargs="?", default=60)
parser.add_argument("frames", type=int, nargs="?", default=1000)
parser.add_argument("change_count", type=int, nargs="?", default=1)
parser.add_argument("change_amount", type=float, nargs="?", default=0.05)
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

def auto_select_loopback():
    print("🎬 Mandala engine starting...")
    devices = sd.query_devices()
    # List all devices for debugging
    for i, dev in enumerate(sd.query_devices()):
        print(f"[{i}] {dev['name']} (inputs: {dev['max_input_channels']}, outputs: {dev['max_output_channels']})")
    
    for i, dev in enumerate(devices):
        name = dev['name'].lower()
        if 'loopback' in name or 'monitor' in name or 'blackhole' in name:
            if dev['max_input_channels'] > 0:
                sd.default.device = (i, i)  # Set both input and output to same loopback device
                print(f"🎧 Using loopback device: {dev['name']}")
                return True
    print("⚠️ No loopback device found. Falling back to microphone.")
    return False

def get_audio_level():
    duration = 0.05
    sample_rate = 44100
    try:
        audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, blocking=True)
        rms = np.sqrt(np.mean(audio**2))
        level = min(rms * 100, 1.0)
        print(f"🔊 Audio level: {level:.3f}")
        return level
    except Exception as e:
        print(f"Audio error: {e}")
        return 0.0

class MandalaParams:
    def __init__(self):
        self.freq_r = random.uniform(0.1, 1.5)
        self.freq_a = random.uniform(1.0, 6.0)
        self.phase_r = random.uniform(0, math.pi * 2)
        self.phase_a = random.uniform(0, math.pi * 2)
        self.offset_x = random.randint(-5, 5)
        self.offset_y = random.randint(-5, 5)
        self.palettes = [
            [' ', '.', '*', '+', 'x', 'X', 'o', 'O', '@', '#'],
            [' ', '-', '=', '~', '^', '*', '%', '$', '&', '#'],
            [' ', '.', ':', ';', '!', '?', '/', '|', '\\', '#'],
            [' ', '·', '•', '*', '¤', '°', '○', '●', '◎', '■'],
            [' ', '˙', '⁕', '✦', '✧', '✶', '✷', '✸', '✺', '✹'],
            [' ', '·', '•', '◦', '○', '◉', '◎', '◍', '◯', '⬤'],
            [' ', '░', '▒', '▓', '▙', '▛', '▜', '▟', '█', '🟥'],
            [' ', '⎯', '⎼', '⎻', '﹏', '╌', '╍', '╏', '╎', '╳'],
            [' ', '☉', '☼', '☽', '☾', '♒', '♓', '♈', '♊', '♋']
        ]
        self.palette_index = random.randint(0, len(self.palettes) - 1)

    @property
    def palette(self):
        return self.palettes[self.palette_index]

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
        return None, None

def generate_frame(params, frame_count, audio_level):
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    hue_shift = frame_count * 2
    brightness = 0.5 + audio_level * 0.5
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
            red   = int((math.sin(hue * 0.03) + 1) * 127 * brightness)
            green = int((math.sin(hue * 0.05 + 2) + 1) * 127 * brightness)
            blue  = int((math.sin(hue * 0.07 + 4) + 1) * 127 * brightness)
            color[y][x] = (int(red), int(green), int(blue))
    return frame, color

def render_frame(prev, curr, colors):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if curr[y][x] != prev[y][x]:
                r, g, b = colors[y][x]
                sys.stdout.write(f"\033[{y+1};{x+1}H\033[38;2;{r};{g};{b}m{curr[y][x]}")
                prev[y][x] = curr[y][x]
    sys.stdout.write("\033[0m")
    sys.stdout.flush()

def display_settings(params, active_param):
    sys.stdout.write(f"\033[{HEIGHT+1};1H\033[0m")
    sys.stdout.write(
        f"🎛 freq_r={params.freq_r:.2f} freq_a={params.freq_a:.2f} "
        f"phase_r={params.phase_r:.2f} phase_a={params.phase_a:.2f} "
        f"offset_x={params.offset_x} offset_y={params.offset_y} "
        f"palette={params.palette_index + 1}/{len(params.palettes)} "
        f"→ animating: {active_param or 'none'}"
    )
    sys.stdout.flush()

def main():
    print("✅ Script started")
    try:
        auto_select_loopback()
        print(f"Using device: {sd.query_devices(sd.default.device)['name']}")
        params = MandalaParams()
        prev_frame = [[' '] * WIDTH for _ in range(HEIGHT)]
        active_param = None
        active_direction = +1
        frame_count = 0

        for _ in range(FRAMES):
            key = get_key()
            if key:
                param, direction = params.mutate(key)
                if param == 'quit':
                    break
                if param:
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

            # Get audio level and generate frame
            # audio_level = get_audio_level()
            curr_frame, colors = generate_frame(params, frame_count, 1)

            # Render and display
            render_frame(prev_frame, curr_frame, colors)
            display_settings(params, active_param)

            time.sleep(DELAY)
            frame_count += 1

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        if not IS_WINDOWS:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_settings)
        sys.stdout.write("\033[?25h\033[0m\n")  # Show cursor, reset
        sys.stdout.flush()

if __name__ == "__main__":
    main()