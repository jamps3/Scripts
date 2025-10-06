from PIL import Image, ImageDraw, ImageFont
import os

# Testattavat fontit "fonts"-kansiossa
font_candidates = [
    os.path.join("fonts", f)
    for f in os.listdir("fonts")
    if f.lower().endswith((".ttf", ".otf"))
]

# Unicode-merkit joita haluat testata
test_lines = [
    ['⬤', '✦', '✧', '✶', '✷', '✸', '✺', '✹', '■', '╳'],
    [' ', '.', '*', '+', 'x', 'X', 'o', 'O', '@', '#'],
    [' ', '-', '=', '~', '^', '*', '%', '$', '&', '#'],
    [' ', '.', ':', ';', '!', '?', '/', '|', '\\', '#'],
    [' ', '·', '•', '*', '¤', '°', '○', '●', '◎', '■'],
    [' ', '˙', '⁕', '✦', '✧', '✶', '✷', '✸', '✺', '✹'],
    [' ', '·', '•', '◦', '○', '◉', '◎', '◍', '◯', '⬤'],
    [' ', '░', '▒', '▓', '▀', '▙', '▛', '▜', '▟', '█'],
    [' ', '⎯', '⎼', '⎻', '﹏', '╌', '╍', '╏', '╎', '╳']
]

from fontTools.ttLib import TTFont

def font_has_glyph(font_path, ch):
    try:
        font = TTFont(font_path)
        for table in font['cmap'].tables:
            if ord(ch) in table.cmap:
                return True
    except:
        pass
    return False

def render_font_preview(font_path, output_file="font_preview.png"):
    try:
        font = ImageFont.truetype(font_path, 32)
    except Exception as e:
        print(f"⚠️ Fontin lataus epäonnistui: {font_path} → {e}")
        return

    font_name = font.getname()[0]
    char_width, char_height = 40, 50
    padding_top = 60
    img_width = char_width * len(test_lines[0])
    img_height = padding_top + char_height * len(test_lines)

    image = Image.new("RGB", (img_width, img_height), (30, 30, 30))
    draw = ImageDraw.Draw(image)

    # Fontin nimi yläreunaan
    draw.text((10, 10), f"Fontti: {font_name}", font=ImageFont.truetype(font_path, 24), fill=(200, 200, 200))

    # Piirrä merkit ja tarkista tuki
    unsupported = []
    for row_index, line in enumerate(test_lines):
        for col_index, ch in enumerate(line):
            x = col_index * char_width
            y = padding_top + row_index * char_height

            if ch == ' ':
                draw.text((x, y), ch, font=font, fill=(255, 255, 255))
            elif not font_has_glyph(font_path, ch):
                draw.text((x, y), ch, font=font, fill=(255, 0, 0))  # punainen = ei löydy fontista
                unsupported.append(ch)
            else:
                draw.text((x, y), ch, font=font, fill=(255, 255, 255))

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    image.save(output_file)
    print(f"✅ Renderöity fontti: {font_name} → {output_file}")
    if unsupported:
        print("❌ Merkkejä ei renderöity:")
        for ch in sorted(set(unsupported)):
            code = f"U+{ord(ch):04X}"
            print(f"  {ch} ({code})")
    else:
        print("✅ Kaikki merkit renderöityivät oikein.")


for font_file in font_candidates:
    if os.path.exists(font_file):
        font_name = os.path.splitext(os.path.basename(font_file))[0]
        output_file = f"fonts/{font_name}.png"
        render_font_preview(font_file, output_file)
    else:
        print(f"🔍 Fonttitiedostoa ei löytynyt: {font_file}")
