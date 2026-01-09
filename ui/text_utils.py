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
    Parse a line with markup and render with proper word wrapping across segments.
    Supports:
      *text* → EXIT_COLOR
      %text% → OBJECT_COLOR
      +text+ → PLAYER_INPUT_COLOR
    Wraps at word boundaries; preserves colors.
    Returns (list of arcade.Text objects, total height including all wrapped lines).
    """
    texts = []
    total_height = 0.0
    current_y = y
    current_x = x
    current_line_height = 0.0
    current_line_texts = []

    # Step 1: Parse markup into colored segments (unchanged)
    parts = []
    i = 0
    while i < len(line):
        if line[i] in '*+%':
            delimiter = line[i]
            j = line.find(delimiter, i + 1)
            if j != -1:
                highlighted = line[i + 1:j]
                color = (
                    EXIT_COLOR if delimiter == '*' else
                    OBJECT_COLOR if delimiter == '%' else
                    PLAYER_INPUT_COLOR
                )
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

    # Step 2: Tokenize parts into words and spaces
    tokens = []
    for text_part, color in parts:
        i = 0
        while i < len(text_part):
            if text_part[i].isspace():
                j = i
                while j < len(text_part) and text_part[j].isspace():
                    j += 1
                tokens.append(('space', text_part[i:j], color))  # Color unused for spaces
                i = j
            else:
                j = i
                while j < len(text_part) and not text_part[j].isspace():
                    j += 1
                tokens.append(('word', text_part[i:j], color))
                i = j

    # Step 3: Get space width (measure once)
    space_measure = arcade.Text(' ', 0, 0, TEXT_COLOR, font_size, font_name)
    space_width = space_measure.content_width

    # Step 4: Layout tokens word-by-word
    for token_type, text, color in tokens:
        if token_type == 'space':
            # Add space width if it fits (trim at line ends/starts)
            add_width = len(text) * space_width
            if current_x + add_width > x + width:
                continue
            current_x += add_width
            continue

        # Word: measure (single-line, no wrap)
        measure_txt = arcade.Text(
            text,
            0, 0,
            color=color,
            font_size=font_size,
            font_name=font_name,
            width=width,
            multiline=True
        )
        word_width = measure_txt.content_width

        # If word doesn't fit, wrap to new line
        if current_x + word_width > x + width:
            texts.extend(current_line_texts)
            if current_line_texts:
                total_height += current_line_height # + LINE_SPACING
                current_y -= current_line_height # + LINE_SPACING
            current_x = x
            current_line_texts = []
            current_line_height = 0.0

        # Place word
        txt = arcade.Text(
            text,
            current_x,
            current_y,
            color=color,
            font_size=font_size,
            font_name=font_name,
            width=width,                  # ← Restores proper font rendering & layout
            multiline=True,               # ← Enables full text engine (even for single words)
            anchor_y="top",
            anchor_x="left"
        )

        current_line_texts.append(txt)
        current_x += word_width
        current_line_height = max(current_line_height, txt.content_height)

    # Commit final line
    if current_line_texts:
        texts.extend(current_line_texts)
        total_height += current_line_height

    return texts, total_height