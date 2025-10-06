"""
ASCII Mandala Generator — Terminal-based animated art engine.

This script renders dynamic, colorized ASCII mandalas directly in the terminal.
It supports real-time parameter control via keyboard input, including frequency,
phase, palette selection, animation speed, and frame capture.

Features:
- Live animation with smooth transitions and color shifting
- Interactive controls for geometry and palette
- Freeze/unfreeze toggle
- Frame capture as PNG
- Animation export as GIF
- Animation export as PNG sequence
- Cross-platform support (Windows, Linux, macOS)

Usage:
    python ascii_mandala.py [width] [height] [fps] [frames] [palette] [change_count] [change_amount]

Example:
    python ascii_mandala.py 120 40 60 5000 6 2 0.2

Controls:
    w/s = freq_r ±       a/d = freq_a ±
    i/k = phase_a ±      j/l = phase_r ±
    p   = next palette   1–8 = select palette
    r   = randomize all  space = freeze/unfreeze
    f   = save PNG       x = export GIF
    +/– = speed control  h = show help
    q   = quit           v = export PNG sequence

Designed for expressive terminal art and joyful experimentation.
"""

import math, random, sys, os, time, argparse, platform
import subprocess
import sys
import platform

# List of required libraries for all platforms
required_libraries = [
    ("PIL", "Pillow"),
    ("fontTools", "fonttools"),
]

# --- Install missing libraries ---
def install_missing_libraries():
    # Install common libraries
    for import_name, package_name in required_libraries:
        try:
            __import__(import_name)
        except ImportError:
            print(f"⚠️ Missing library: {package_name}. Installing now...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

    # Platform-specific libraries
    #if platform.system() == "Windows":
    #elif platform.system() == "Linux":

# Install missing libraries before running the main program
install_missing_libraries()

# Now import the libraries (they should be installed now)
from PIL import ImageFont
from fontTools.ttLib import TTFont

# OS detection
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import msvcrt
else:
    import termios, tty, select

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("width", type=int, nargs="?", default=120, help="Width in characters")
parser.add_argument("height", type=int, nargs="?", default=24, help="Height in characters")
parser.add_argument("fps", type=int, nargs="?", default=50, help="Frames per second")
parser.add_argument("frames", type=int, nargs="?", default=10000, help="Total frames to display")
parser.add_argument("palette", type=int, nargs="?", default=0, help="Palette index (1–8)")
parser.add_argument("change_count", type=int, nargs="?", default=1, help="Number of parameters to change simultaneously")
parser.add_argument("change_amount", type=float, nargs="?", default=0.05, help="Amount to change parameters by")
args = parser.parse_args()

WIDTH, HEIGHT = args.width, args.height
FPS, FRAMES = args.fps, args.frames
CHANGE_COUNT = args.change_count
CHANGE_AMOUNT = [args.change_amount]  # wrap in list
DELAY = 1.0 / FPS
recording = [False]  # wrapped in list for mutability
frames = [] # For storing animation frames for export

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

def show_controls_inline():
    sys.stdout.write("\033[1;1H\033[2K\033[0m")  # Clear line 1
    sys.stdout.write(
        "🎮 w/s=freq_r a/d=freq_a i/k=phase_a j/l=phase_r p=next_palette 1–8=select_palette r=randomize space=freeze"
    )
    sys.stdout.write("\n+/–=speed h=help q=quit f=export PNG c=toggle capture x=export GIF v=export PNG sequence")
    sys.stdout.flush()

def font_has_glyph(font_path, ch):
    try:
        font = TTFont(font_path)
        for table in font['cmap'].tables:
            if ord(ch) in table.cmap:
                return True  # Found the glyph
    except Exception:
        pass
    return False

def find_best_font(palettes, font_dir="fonts"):
    # Etsii fonts-kansiosta fontin, joka tukee eniten annettuja merkkejä kaikista paleteista
    font_candidates = [
        os.path.join(font_dir, f)
        for f in os.listdir(font_dir)
        if f.lower().endswith((".ttf", ".otf"))  # Hae kaikki .ttf ja .otf fontit
    ]

    best_font = None
    max_supported = -1

    print("Tarkistetaan fonttien symbolitukea...")

    for font_path in font_candidates:
        try:
            font = TTFont(font_path)
        except Exception as e:
            print(f"⚠️ Virhe ladattaessa fonttia {font_path}: {e}")
            continue

        supported = 0
        for palette_line in palettes:
            for ch in palette_line:
                if ch == ' ' or font_has_glyph(font_path, ch):
                    supported += 1
        # Laske palettes kaikki merkit
        total_chars = sum(len(line) for line in palettes)
        print(f"🔍 {os.path.basename(font_path)} tukee {supported}/{total_chars} merkkiä")
        if supported > max_supported:
            max_supported = supported
            best_font = font_path

    if best_font:
        print(f"\n✅ Paras fontti: {os.path.basename(best_font)} ({max_supported}/{total_chars} merkkiä tuettu)")
    else:
        print("❌ Yksikään fontti ei tue annettuja merkkejä")

    return best_font

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
            [' ', '░', '▒', '▓', '▙', '▛', '▜', '▟', '█', '■'],
            [' ', '⎯', '⎼', '⎻', '﹏', '╌', '╍', '╏', '╎', '╳']
        ]
        self.palette_index = max(0, min(palette_index, len(self.palettes) - 1))
        self.transition_frames = 0
        self.target_palette_index = self.palette_index
        self.font_name = "fonts/Symbola.ttf"
        self.font_size = 14

    @property
    def palette(self):
        return self.get_blended_palette()

    def mutate(self, key):
        if key == ' ':  # Toggle freeze
            return 'toggle_freeze', None
        if key == 'q': return 'quit', None  # Quit program
        if key == 'w': self.freq_r += CHANGE_AMOUNT[0]; return 'freq_r', +1
        if key == 's': self.freq_r -= CHANGE_AMOUNT[0]; return 'freq_r', -1
        if key == 'a': self.freq_a -= CHANGE_AMOUNT[0] * 2; return 'freq_a', -1
        if key == 'd': self.freq_a += CHANGE_AMOUNT[0] * 2; return 'freq_a', +1
        if key == 'j': self.phase_r += CHANGE_AMOUNT[0] * 3; return 'phase_r', +1
        if key == 'l': self.phase_r -= CHANGE_AMOUNT[0] * 3; return 'phase_r', -1
        if key == 'i': self.phase_a += CHANGE_AMOUNT[0] * 3; return 'phase_a', +1
        if key == 'k': self.phase_a -= CHANGE_AMOUNT[0] * 3; return 'phase_a', -1
        if key == 'p': self.palette_index = (self.palette_index + 1) % len(self.palettes); return 'palette', +1
        if key == 'f':
            return 'freeze_capture', None
        if key == 'c':
            return 'toggle_capture', None
        if key == 'x':
            return 'export_gif', None
        if key == 'v':
            return 'export_png_sequence', None
        if key == 'r':
            self.randomize()
            return 'randomize', None
        if key in '12345678':
            self.target_palette_index = int(key) - 1
            self.transition_frames = 30  # Palette transition over 30 frames
            return 'palette', 0
        if key == '+':
            return 'speed_up', None
        if key == '-':
            return 'slow_down', None
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
    
    def randomize(self):
        self.freq_r = random.uniform(0.1, 1.5)
        self.freq_a = random.uniform(1.0, 6.0)
        self.phase_r = random.uniform(0, math.pi * 2)
        self.phase_a = random.uniform(0, math.pi * 2)
        self.offset_x = random.randint(-5, 5)
        self.offset_y = random.randint(-5, 5)
        # self.target_palette_index = random.randint(0, len(self.palettes) - 1)
        self.transition_frames = 30

def generate_frame(params, frame_count):
    """
    Generates a single ASCII mandala frame and its corresponding RGB color matrix.

    Args:
        params (MandalaParams): Current mandala parameters including frequencies, phases, offsets, and palette.
        frame_count (int): Frame number used for animation and color shifting.

    Returns:
        tuple:
            frame (list[list[str]]): 2D grid of ASCII characters for each position.
            color (list[list[tuple[int, int, int]]]): 2D grid of RGB tuples for each character position.

    The function computes each cell's value using polar coordinates and trigonometric transformations,
    maps the result to a character from the current palette, and generates a corresponding RGB color
    for dynamic, animated rendering.
    """

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
    RESERVED_LINES = 1  # Lines reserved for controls and status
    for y in range(HEIGHT - RESERVED_LINES):
        for x in range(WIDTH):
            if curr[y][x] != prev[y][x]:
                r, g, b = colors[y][x]
                sys.stdout.write(f"\033[{y+3};{x+1}H\033[38;2;{r};{g};{b}m{curr[y][x]}")
                prev[y][x] = curr[y][x]
    sys.stdout.write("\033[0m")
    sys.stdout.flush()

from PIL import Image, ImageDraw, ImageFont

def save_frame_as_png(frame, colors, font_path, filename="mandala_capture.png"):
    char_width, char_height = 10, 18  # adjust for font size
    img_width = WIDTH * char_width
    img_height = HEIGHT * char_height
    image = Image.new("RGB", (img_width, img_height), (0, 0, 0))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype(font_path, 14)
    except:
        font = ImageFont.load_default()

    for y in range(HEIGHT):
        for x in range(WIDTH):
            ch = frame[y][x]
            r, g, b = colors[y][x]
            draw.text((x * char_width, y * char_height), ch, fill=(r, g, b), font=font)

    image.save(filename)

def save_frame_as_png_sequence(frame, colors, frame_index, font_path, output_dir="frames"):
    char_width, char_height = 10, 18
    img = Image.new("RGB", (WIDTH * char_width, HEIGHT * char_height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, 14)
    except:
        font = ImageFont.load_default()

    for y in range(HEIGHT):
        for x in range(WIDTH):
            ch = frame[y][x]
            r, g, b = colors[y][x]
            draw.text((x * char_width, y * char_height), ch, fill=(r, g, b), font=font)

    os.makedirs(output_dir, exist_ok=True)
    
    for i, img in enumerate(frames):
        filename = os.path.join(output_dir, f"frame_{i:04d}.png")
        img.save(filename)
    
    print(f"✅ Saved {len(frames)} frames as PNG sequence in '{output_dir}'")

def capture_frame(frame, colors, font_path):
    from PIL import Image, ImageDraw, ImageFont
    char_width, char_height = 10, 18
    img = Image.new("RGB", (WIDTH * char_width, HEIGHT * char_height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, 14)
    except:
        font = ImageFont.load_default()

    for y in range(HEIGHT):
        for x in range(WIDTH):
            ch = frame[y][x]
            r, g, b = colors[y][x]
            draw.text((x * char_width, y * char_height), ch, fill=(r, g, b), font=font)

    frames.append(img)

def export_gif():
    if not frames:
        return
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"mandala_{timestamp}.gif"  # Timestamped filename
    duration_ms = max(1, int(round(1000 / FPS)))  # 1 ms minimum
    frames[0].save(
        filename,  # output filename
        save_all=True,  # Save all frames
        append_images=frames[1:],   # Append all captured frames
        duration=duration_ms,  # Duration per frame in ms
        loop=0,  # Loop forever
        optimize=False,  # Optimize GIF size (rendering), disabled because it loses quality
        transparency=0  # Set transparency color index
    )
    frames.clear()

# --- Display currently used settings ---
def display_settings(params, active_param, frozen, recording):
    sys.stdout.write(f"\033[{HEIGHT+3};1H\033[2K\033[0m")  # Clear line below settings
    sys.stdout.write(
        f"🎛 freq_r={params.freq_r:.2f} freq_a={params.freq_a:.2f} "
        f"phase_r={params.phase_r:.2f} phase_a={params.phase_a:.2f} "
        f"offset_x={params.offset_x} offset_y={params.offset_y} "
        f"palette={params.palette_index + 1}/{len(params.palettes)} "
        f"→ {active_param or 'none'} speed={CHANGE_AMOUNT[0]:.3f}"
    )
    frozen_text = "⏸ frozen" if frozen else "▶ running"
    palette_preview = ''.join(params.palette)
    recording_text = "🎥 recording" if recording[0] else "⏹ not recording"
    recording_text += f" ({len(frames)} frames captured)"
    sys.stdout.write(f"\033[{HEIGHT+2};1H\033[2K\033[0m")  # Clear line below settings
    sys.stdout.write(f"🧵 Palette: {palette_preview}  {frozen_text} {recording_text} Font: {params.font_name}")
    sys.stdout.flush()

def main():
    params = MandalaParams(palette_index=args.palette - 1)
    prev_frame = [[' '] * WIDTH for _ in range(HEIGHT)]
    active_param = None
    active_direction = 0  # no animation until a key sets it
    frame_count = 0
    frozen = True  # Start frozen until user interaction)
    # Select font that supports the most characters in all palettes
    best_font_path = find_best_font(params.palettes)
    input("Press Enter to continue...")  # Wait for a key press before proceeding
    sys.stdout.write("\033[2J\033[H")  # Clear screen and move cursor to home
    sys.stdout.flush()
    # Show controls
    show_controls_inline()
    params.font_name = os.path.splitext(os.path.basename(best_font_path))[0]

    try:
        for _ in range(FRAMES):  # Animate for a set number of frames
            start_time = time.time()  # Timer: count how long this function takes to execute
            key = get_key()
            if key:
                param, direction = params.mutate(key)
                if param == 'toggle_freeze':
                    if active_param and active_direction:
                        frozen = not frozen
                elif param == 'speed_up':
                    CHANGE_AMOUNT[0] *= 1.2
                elif param == 'slow_down':
                    CHANGE_AMOUNT[0] /= 1.2
                elif param == 'freeze_capture':
                    import datetime
                    filename = f"mandala_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    save_frame_as_png(curr_frame, colors, best_font_path, filename)
                elif param == 'toggle_capture':
                    recording[0] = not recording[0]
                elif param == 'export_gif':
                    export_gif()
                elif param == 'export_png_sequence':
                    save_frame_as_png_sequence(curr_frame, colors, frame_count, best_font_path)
                elif param == 'quit':
                    break
                elif param == 'help':
                    show_controls_inline()
                elif param:
                    if param not in ['palette', 'randomize']:  # prevent palette and randomize from being animated
                        active_param = param
                        active_direction = direction

            # Animate active parameters when not frozen
            if not frozen and active_param and active_direction:
                delta = CHANGE_AMOUNT[0] * active_direction
                if active_param == 'freq_r': params.freq_r += delta
                elif active_param == 'freq_a': params.freq_a += delta * 2
                elif active_param == 'phase_r': params.phase_r += delta * 3
                elif active_param == 'phase_a': params.phase_a += delta * 3
                elif active_param == 'offset_x': params.offset_x += int(delta * 10)
                elif active_param == 'offset_y': params.offset_y += int(delta * 10)

            curr_frame, colors = generate_frame(params, frame_count)
            display_settings(params, active_param, frozen, recording)
            render_frame(prev_frame, curr_frame, colors)
            if recording[0]:
                capture_frame(curr_frame, colors, font_path=params.font_name)
            sleep_time = max(0, DELAY - (time.time() - start_time))  # Adjust sleep to maintain consistent FPS. Ensure sleep time is non-negative.
            time.sleep(sleep_time)
            # start_time = time.time()  # Reset timer for next frame
            percentleft = int(round((sleep_time / DELAY) * 100))
            sys.stdout.write(f"\033[{HEIGHT+4};1H\033[2KFrame time left: {percentleft}% - {sleep_time:.4f}s")
            sys.stdout.flush()
            frame_count += 1
    except KeyboardInterrupt:
        pass
    finally:
        if not IS_WINDOWS:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_settings)
        sys.stdout.write("\033[?25h\033[0m\n")  # Show cursor, reset
        sys.stdout.flush()

main()