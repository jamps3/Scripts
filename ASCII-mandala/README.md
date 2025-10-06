# ASCII Mandala Generator — Terminal-based animated art engine.
![ASCII Mandala screenshot](https://github.com/jamps3/Scripts/blob/master/ASCII-mandala/screenshot.png)

This script renders dynamic, colorized ASCII mandalas directly in the terminal.
It supports real-time parameter control via keyboard input, including frequency,
phase, palette selection, animation speed, and frame capture.

## Features:
- Live animation with smooth transitions and color shifting
- Interactive controls for geometry and palette
- Freeze/unfreeze toggle
- Frame capture as PNG
- Animation export as GIF
- Animation export as PNG sequence
- Cross-platform support (Windows, Linux, macOS)

## Exported video
<video src="animation.mp4" autoplay loop muted playsinline controls width="640">
  Your browser does not support the video tag.
</video>

## Usage:
    python ascii_mandala.py [width] [height] [fps] [frames] [palette] [change_count] [change_amount]

## Example:
    python ascii_mandala.py 120 40 60 5000 6 2 0.2

Controls:
    w/s = freq_r ±       a/d = freq_a ±
    i/k = phase_a ±      j/l = phase_r ±
    p   = next palette   1–8 = select palette
    r   = randomize all  space = freeze/unfreeze
    f   = save PNG       x = export GIF
    +/– = speed control  h = show help
    q   = quit

Designed for expressive terminal art and joyful experimentation.
