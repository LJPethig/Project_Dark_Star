# ui/text_utils.py
import arcade
from constants import *

def parse_markup_line(
    line: str,
    x: float,
    y: float,
    width: float,
    font_size: int = DESCRIPTION_FONT_SIZE,
    font_name: str = FONT_NAME_PRIMARY
) -> tuple[list[arcade.Text], float]:
    """
    Parse a single line with markup:
    *text* → cyan (ACCENT_COLOR)
    %text% → purple (OBJECT_COLOR)
    +text+ → yellow (PLAYER_INPUT_COLOR)
    Returns (list of arcade.Text objects for the line, max line height used).
    """
    texts = []
    parts = []
    i = 0
    while i < len(line):
        if line[i] in '*+%':
            delimiter = line[i]
            j = line.find(delimiter, i + 1)
            if j != -1:
                highlighted = line[i + 1:j]
                if delimiter == '*':
                    color = ACCENT_COLOR
                elif delimiter == '%':
                    color = OBJECT_COLOR
                elif delimiter == '+':
                    color = PLAYER_INPUT_COLOR
                parts.append((highlighted, color))
                i = j + 1
                continue
        # Normal text up to next delimiter
        next_pos = len(line)
        for delim in '*+%':
            pos = line.find(delim, i)
            if pos != -1 and pos < next_pos:
                next_pos = pos
        normal = line[i:next_pos]
        if normal:
            parts.append((normal, TEXT_COLOR))
        i = next_pos

    x_pos = x
    line_height = 0
    for text_part, color in parts:
        if not text_part.strip():
            continue
        txt = arcade.Text(
            text_part,
            x=x_pos,
            y=y,
            color=color,
            font_size=font_size,
            font_name=font_name,
            width=width,
            multiline=True,
            anchor_y="top",
            anchor_x="left"
        )
        texts.append(txt)
        x_pos += txt.content_width
        line_height = max(line_height, txt.content_height)

    return texts, line_height