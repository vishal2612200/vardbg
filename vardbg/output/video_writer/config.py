import collections.abc
from pathlib import Path
import math

import toml
from pygments.formatter import Formatter
from vardbg.assets.styles.default import DefaultStyle
from pygments.token import Token

FILE_PATH = Path(__file__).parent
ASSETS_PATH = FILE_PATH / ".." / ".." / "assets"
DEFAULT_CFG_PATH = FILE_PATH / "default_config.toml"

# List for colors in color_scheme
color_list = []

# Source: https://stackoverflow.com/a/3233356
def recursive_update(base, new):
    for k, v in new.items():
        if isinstance(v, collections.abc.Mapping):
            base[k] = recursive_update(base.get(k, {}), v)
        else:
            base[k] = v

    return base


def load_data(path):
    base = toml.loads(DEFAULT_CFG_PATH.read_text())

    # Just return default if there's no custom data
    if not path:
        return base

    # Load and merge custom data
    overlay = toml.loads(Path(path).read_text())
    recursive_update(base, overlay)
    return base


def sub_path(path):
    # Expand $ASSETS to asset directory
    if path.startswith("$ASSETS"):
        path = path.replace("$ASSETS", str(ASSETS_PATH), 1)

    return path


def calc_frac(value, frac):
    num, denom = frac
    return round(value * num / denom)


def parse_hex_color(string):
    if string.startswith("#"):
        string = string[1:]

    r = int(string[0:2], 16)
    g = int(string[2:4], 16)
    b = int(string[4:6], 16)

    return r, g, b, 255

# Some color_scheme can have same txt and bg color
def color_contrast(body_txt):
    contrast = (int(body_txt[0] * 299) + int(body_txt[1] * 587) + int(body_txt[2] * 114)) / 1000
    if (contrast >= 128):  
        return (50,50,50,255) # return grey
    else:
        return (255,255,255,255) # return white

# Calculate distance btw two color
def color_similarity(base_col_val,oth_col_val):
    return math.sqrt(sum((base_col_val[i]-oth_col_val[i])**2 for i in range(3)))

def load_style(style):
    styles = {}
    formatter = Formatter(style=style)

    for token, params in formatter.style:
        color = parse_hex_color(params["color"]) if params["color"] else None

        # Save style
        styles[token] = {"color": color}

    return styles


class Config:
    def __init__(self, config_path):
        # Load config
        self.data = load_data(config_path)

        # Extract values
        general = self.data["general"]
        self.w = general["width"]
        self.h = general["height"]
        self.fps = general["fps"]

        self.intro_text = general["intro_text"]
        self.intro_time = general["intro_time"]
        self.watermark = general["watermark"]

        sizes = self.data["sizes"]
        self.var_x = calc_frac(self.w, sizes["code_width"])
        self.out_y = calc_frac(self.h, sizes["code_height"])
        self.ovar_y = calc_frac(self.h, sizes["last_variable_height"])

        self.head_padding = sizes["heading_padding"]
        self.sect_padding = sizes["section_padding"]

        self.line_height = sizes["line_height"]

        fonts = self.data["fonts"]
        self.font_body = (sub_path(fonts["body"]), fonts["body_size"])
        self.font_body_bold = (sub_path(fonts["body_bold"]), fonts["body_size"])
        self.font_caption = (sub_path(fonts["caption"]), fonts["caption_size"])
        self.font_heading = (sub_path(fonts["heading"]), fonts["heading_size"])
        self.font_intro = (sub_path(fonts["intro"]), fonts["intro_size"])

        style = DefaultStyle
        self.styles = load_style(style)

        self.bg = parse_hex_color(style.background_color)
        self.highlight = parse_hex_color(style.highlight_color)
        self.fg_divider = self.styles[Token.Generic.Subheading]["color"]
        self.fg_heading = self.styles[Token.Name]["color"]
        self.fg_body = color_contrast(self.bg)
        self.fg_watermark = self.styles[Token.Comment]["color"]
        
        self.red = self.styles[Token.Operator]["color"]
        self.green = self.styles[Token.Name.Function]["color"]
        self.blue = self.styles[Token.Keyword]["color"]
