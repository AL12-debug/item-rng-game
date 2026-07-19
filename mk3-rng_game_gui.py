"""
RNG Item Roller Game - GUI Edition (Restyled)
----------------------------------------------
A tabbed desktop GUI built with tkinter (included with Python, no installs
needed). Modern dark theme, color-coded rarities, card layouts, and custom
flat buttons with hover effects.

Run with:  python3 rng_game_gui.py
"""

import random
import math
import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter

# ---------------------------------------------------------------------------
# Palette (dark, muted, Catppuccin-inspired)
# ---------------------------------------------------------------------------

PALETTE = {
    "base":     "#1e1e2e",
    "mantle":   "#181825",
    "surface0": "#292c3c",
    "surface1": "#363a4f",
    "surface2": "#494d64",
    "text":     "#cdd6f4",
    "subtext":  "#9399b2",
    "accent":   "#cba6f7",   # mauve
    "accent_hover": "#b48ff0",
    "green":    "#a6e3a1",
    "blue":     "#89b4fa",
    "yellow":   "#f9e2af",
    "peach":    "#fab387",
    "red":      "#f38ba8",
    "maroon":   "#eba0ac",
    "white":    "#f5f7ff",
    "gold_glow": "#ffe08a",
    "sapphire": "#74c7ec",
}

# ---------------------------------------------------------------------------
# Game configuration
# ---------------------------------------------------------------------------

RARITIES = {
    "Common":     {"weight": 60,     "color": PALETTE["subtext"],  "sell_value": 1},
    "Good":       {"weight": 25,     "color": PALETTE["green"],    "sell_value": 3},
    "Rare":       {"weight": 10,     "color": PALETTE["blue"],     "sell_value": 8},
    "Super Rare": {"weight": 4,      "color": PALETTE["accent"],   "sell_value": 20},
    "Legendary":  {"weight": 1,      "color": PALETTE["yellow"],   "sell_value": 50},
    "Mythical":   {"weight": 0.3,    "color": PALETTE["maroon"],   "sell_value": 150},
    "Godlike":    {"weight": 0.05,   "color": PALETTE["gold_glow"],"sell_value": 500},
    "Secret":     {"weight": 0.004,  "color": PALETTE["sapphire"], "sell_value": 5000},
}

ITEM_POOL = {
    "Common": [
        "Rusty Sword", "Wooden Shield", "Leather Boots", "Stale Bread",
        "Small Health Potion", "Torn Cloak",
    ],
    "Good": [
        "Iron Sword", "Steel Shield", "Traveler's Cloak", "Silver Ring",
        "Medium Health Potion",
    ],
    "Rare": [
        "Enchanted Blade", "Knight's Armor", "Ring of Vigor", "Phoenix Feather",
    ],
    "Super Rare": [
        "Dragonfang Sword", "Aegis of the Titans", "Crown of Storms",
    ],
    "Legendary": [
        "Excalibur", "The Godslayer", "Infinity Core",
    ],
    "Mythical": [
        "Voidblade", "Chrono Amulet", "Starforged Crown", "Eclipse Ring",
    ],
    "Godlike": [
        "Hand of Creation", "The Absolute", "Genesis Blade",
    ],
    "Secret": [
        "The Singularity", "Origin", "???",
    ],
}

ROLL_COST = 1
STARTING_CURRENCY = 20

# Rarities dramatic enough to earn a full cutscene, with intensity that
# escalates the higher the tier goes. hold_ms controls how long the
# cutscene stays on screen before auto-continuing (the player can always
# click/press a key to skip early).
CUTSCENE_CONFIG = {
    "Super Rare": {"title": "SUPER RARE!",  "rings": 3, "particles": 18, "hold_ms": 3400, "title_size": 30},
    "Legendary":  {"title": "LEGENDARY!",   "rings": 4, "particles": 24, "hold_ms": 4200, "title_size": 32},
    "Mythical":   {"title": "MYTHICAL!!",   "rings": 5, "particles": 30, "hold_ms": 5000, "title_size": 34},
    "Godlike":    {"title": "★ GODLIKE ★",  "rings": 6, "particles": 38, "hold_ms": 5800, "title_size": 36},
    "Secret":     {"title": "✦ ✦ SECRET ✦ ✦", "rings": 8, "particles": 50, "hold_ms": 7000, "title_size": 38},
}

# Each item gets its own animated flourish layered into the cutscene, on
# top of the shared burst-ring/particle base, so pulling a sword feels
# different from pulling a ring or a crown. Anything not listed falls
# back to the generic "pulse" style.
ITEM_ANIMATION_STYLE = {
    "Dragonfang Sword":    "slash",
    "Excalibur":           "slash",
    "The Godslayer":       "slash",
    "Genesis Blade":       "slash",
    "Aegis of the Titans": "starburst",
    "Crown of Storms":     "halo",
    "Starforged Crown":    "halo",
    "Infinity Core":       "pulse",
    "Chrono Amulet":       "pulse",
    "Voidblade":           "vortex",
    "Eclipse Ring":        "orbit",
    "Hand of Creation":    "divine",
    "The Absolute":        "divine",
    "The Singularity":     "divine",
    "Origin":              "divine",
    "???":                 "vortex",
}

# ---------------------------------------------------------------------------
# Shop system
# ---------------------------------------------------------------------------

SHOP_REFRESH_SECONDS = 300  # 5 minutes
SHOP_SLOT_COUNT = 4

# Which rarities get their odds boosted for each scope tier. Boosting a
# rarity's weight relative to the others (without touching Common) shifts
# the real odds in the player's favor.
SCOPE_RARITIES = {
    "Good+":        ["Good", "Rare", "Super Rare", "Legendary", "Mythical", "Godlike", "Secret"],
    "Rare+":        ["Rare", "Super Rare", "Legendary", "Mythical", "Godlike", "Secret"],
    "Super Rare+":  ["Super Rare", "Legendary", "Mythical", "Godlike", "Secret"],
    "Legendary+":   ["Legendary", "Mythical", "Godlike", "Secret"],
    "Mythical+":    ["Mythical", "Godlike", "Secret"],
    "Godlike+":     ["Godlike", "Secret"],
}

# Templates the shop draws from each refresh. Each restock rolls random
# stats (boost %, duration, price) within these ranges, so the same potion
# name can show up with different numbers cycle to cycle.
POTION_CATALOG = [
    {"name": "Traveler's Charm",  "base_price": 18,  "boost_range": (8, 18),   "duration_range": (10, 18), "scope": "Good+"},
    {"name": "Minor Luck Potion", "base_price": 25,  "boost_range": (12, 25),  "duration_range": (6, 12),  "scope": "Good+"},
    {"name": "Fortune Elixir",    "base_price": 45,  "boost_range": (20, 40),  "duration_range": (5, 10),  "scope": "Rare+"},
    {"name": "Mystic Brew",       "base_price": 75,  "boost_range": (30, 60),  "duration_range": (4, 8),   "scope": "Super Rare+"},
    {"name": "Godly Tonic",       "base_price": 150, "boost_range": (50, 100), "duration_range": (3, 6),   "scope": "Legendary+"},
    {"name": "Ascendant Elixir",  "base_price": 300, "boost_range": (75, 150), "duration_range": (2, 5),   "scope": "Mythical+"},
]

# ---------------------------------------------------------------------------
# Crafting system
# ---------------------------------------------------------------------------

# Gauntlets/Artifacts you build from raw materials (rolled items diverted
# away from your sellable collection). Effects are PERMANENT once crafted,
# unlike shop potions which wear off after a set number of rolls.
# materials: dict of rarity -> quantity required (dict order = display order,
# low-to-high, so the last key is treated as the "signature" rarity/color).
# effect: either a luck boost ("kind": "luck") that shifts odds for a scope
# of rarities, or a permanent sell bonus ("kind": "sell_bonus").
CRAFTING_RECIPES = [
    {
        "name": "Gauntlet of the Novice", "type": "Gauntlet",
        "materials": {"Common": 10},
        "effect": {"kind": "luck", "scope": "Good+", "boost_pct": 8},
        "desc": "A basic gauntlet forged from common scraps.",
    },
    {
        "name": "Gauntlet of Greed", "type": "Gauntlet",
        "materials": {"Common": 6, "Good": 4},
        "effect": {"kind": "sell_bonus", "pct": 15},
        "desc": "Every sale feels a little more generous.",
    },
    {
        "name": "Gauntlet of the Hunt", "type": "Gauntlet",
        "materials": {"Good": 6, "Rare": 3},
        "effect": {"kind": "luck", "scope": "Rare+", "boost_pct": 18},
        "desc": "Sharpens your instincts for rare finds.",
    },
    {
        "name": "Artifact of Ascension", "type": "Artifact",
        "materials": {"Rare": 5, "Super Rare": 2},
        "effect": {"kind": "luck", "scope": "Super Rare+", "boost_pct": 28},
        "desc": "Hums with barely-contained power.",
    },
    {
        "name": "Artifact of Eternity", "type": "Artifact",
        "materials": {"Super Rare": 3, "Legendary": 1},
        "effect": {"kind": "luck", "scope": "Legendary+", "boost_pct": 40},
        "desc": "Said to bend fate itself.",
    },
]

# ---------------------------------------------------------------------------
# Biomes — a passive, free-to-everyone luck effect that rotates on its own
# timer (unlike shop potions, which cost coins and you choose to buy).
# Weighted so the wild, powerful biomes show up rarely, encouraging players
# to time their rolls around a good one — same idea as Sol's RNG biomes.
# ---------------------------------------------------------------------------
BIOME_ROTATE_SECONDS = 90

BIOMES = [
    {"name": "Normal Biome",    "scope": None,          "boost_pct": 0,   "weight": 50, "color": PALETTE["subtext"]},
    {"name": "Windy Biome",     "scope": "Good+",        "boost_pct": 12,  "weight": 24, "color": PALETTE["green"]},
    {"name": "Starfall Biome",  "scope": "Rare+",        "boost_pct": 28,  "weight": 14, "color": PALETTE["blue"]},
    {"name": "Corrupted Biome", "scope": "Super Rare+",  "boost_pct": 50,  "weight": 7,  "color": PALETTE["accent"]},
    {"name": "Glitched Biome",  "scope": "Legendary+",   "boost_pct": 90,  "weight": 3,  "color": PALETTE["yellow"]},
    {"name": "Null Biome",      "scope": "Mythical+",    "boost_pct": 160, "weight": 1.4, "color": PALETTE["maroon"]},
    {"name": "??? Biome",       "scope": "Godlike+",     "boost_pct": 300, "weight": 0.3, "color": PALETTE["sapphire"]},
]

# ---------------------------------------------------------------------------
# Achievements — one-time milestones that pay out a coin bonus. Checked
# after every roll batch. "check" receives the app instance and returns
# True once the milestone is met.
# ---------------------------------------------------------------------------
ACHIEVEMENTS = [
    {"name": "First Steps", "desc": "Make your first roll.", "reward": 10,
     "check": lambda app: app.total_rolls >= 1},
    {"name": "Getting the Hang of It", "desc": "Make 50 rolls.", "reward": 30,
     "check": lambda app: app.total_rolls >= 50},
    {"name": "Dedicated Roller", "desc": "Make 250 rolls.", "reward": 100,
     "check": lambda app: app.total_rolls >= 250},
    {"name": "Unstoppable", "desc": "Make 1,000 rolls.", "reward": 400,
     "check": lambda app: app.total_rolls >= 1000},
    {"name": "Ooh, Shiny", "desc": "Find your first Super Rare item.", "reward": 25,
     "check": lambda app: app.lifetime_counts.get("Super Rare", 0) >= 1},
    {"name": "Legend in the Making", "desc": "Find your first Legendary item.", "reward": 75,
     "check": lambda app: app.lifetime_counts.get("Legendary", 0) >= 1},
    {"name": "Myth Made Real", "desc": "Find your first Mythical item.", "reward": 200,
     "check": lambda app: app.lifetime_counts.get("Mythical", 0) >= 1},
    {"name": "Divine Intervention", "desc": "Find your first Godlike item.", "reward": 500,
     "check": lambda app: app.lifetime_counts.get("Godlike", 0) >= 1},
    {"name": "???", "desc": "Find a Secret item.", "reward": 2000,
     "check": lambda app: app.lifetime_counts.get("Secret", 0) >= 1},
    {"name": "Blacksmith", "desc": "Craft your first Gauntlet or Artifact.", "reward": 40,
     "check": lambda app: len(app.crafted_gear) >= 1},
    {"name": "Fully Equipped", "desc": "Craft every recipe.", "reward": 300,
     "check": lambda app: len(app.crafted_gear) >= len(CRAFTING_RECIPES)},
]

# ---------------------------------------------------------------------------
# Redeem codes — a small nod to the "enter a code for free stuff" ritual
# from Roblox RNG games. Case-insensitive, each usable once per game.
# ---------------------------------------------------------------------------
REDEEM_CODES = {
    "WELCOME": {"coins": 50},
    "LUCKY7": {"coins": 77},
    "BONUSROLL": {"coins": 120},
    "SECRETSTASH": {"coins": 500},
}

# ---------------------------------------------------------------------------
# Minesweeper minigame — costs coins to play, pays out on a win. Numbers
# use the classic Minesweeper color convention (1=blue, 2=green, etc.).
# ---------------------------------------------------------------------------
MINE_DIFFICULTIES = [
    {"name": "Easy",   "rows": 8,  "cols": 8,  "mines": 10, "cost": 10, "reward": 40},
    {"name": "Medium", "rows": 10, "cols": 10, "mines": 20, "cost": 25, "reward": 120},
    {"name": "Hard",   "rows": 12, "cols": 12, "mines": 30, "cost": 50, "reward": 300},
]

MINE_NUMBER_COLORS = {
    1: PALETTE["blue"], 2: PALETTE["green"], 3: PALETTE["red"], 4: PALETTE["accent"],
    5: PALETTE["maroon"], 6: PALETTE["sapphire"], 7: PALETTE["text"], 8: PALETTE["subtext"],
}

FONT_TITLE = ("Segoe UI", 19, "bold")
FONT_HEADER = ("Segoe UI", 13, "bold")
FONT_BODY = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 10)


def weighted_rarity_choice():
    tiers = list(RARITIES.keys())
    weights = [RARITIES[t]["weight"] for t in tiers]
    return random.choices(tiers, weights=weights, k=1)[0]


def roll_item():
    rarity = weighted_rarity_choice()
    item = random.choice(ITEM_POOL[rarity])
    return rarity, item


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c))) for c in rgb)


def blend_color(color_a, color_b, t):
    """Interpolate between two hex colors. t=0 -> color_a, t=1 -> color_b."""
    r1, g1, b1 = hex_to_rgb(color_a)
    r2, g2, b2 = hex_to_rgb(color_b)
    return rgb_to_hex((r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t))


def rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def make_badge(parent, text, color, bg, fg=PALETTE["mantle"]):
    """A small rounded 'pill' label showing rarity, drawn on a Canvas."""
    font = ("Segoe UI", 10, "bold")
    tmp = tk.Label(parent, text=text, font=font)
    tmp.update_idletasks()
    w, h = tmp.winfo_reqwidth() + 26, tmp.winfo_reqheight() + 10
    tmp.destroy()
    c = tk.Canvas(parent, width=w, height=h, bg=bg, highlightthickness=0)
    rounded_rect(c, 1, 1, w - 1, h - 1, radius=h // 2, fill=color, outline="")
    c.create_text(w // 2, h // 2, text=text, font=font, fill=fg)
    return c


def make_dynamic_badge(parent, text, color, fg=PALETTE["mantle"]):
    """Like make_badge, but returns (canvas, update_fn) so the pill's text
    (and optionally color) can be redrawn in place efficiently — used for
    the animated coin counter and the biome banner."""
    font = ("Segoe UI", 10, "bold")
    parent_bg = parent.cget("bg") if hasattr(parent, "cget") else PALETTE["mantle"]
    canvas = tk.Canvas(parent, bg=parent_bg, highlightthickness=0, bd=0)
    state = {"color": color}

    def update(new_text, new_color=None):
        if new_color:
            state["color"] = new_color
        tmp = tk.Label(parent, text=new_text, font=font)
        tmp.update_idletasks()
        w, h = tmp.winfo_reqwidth() + 26, tmp.winfo_reqheight() + 10
        tmp.destroy()
        canvas.config(width=w, height=h)
        canvas.delete("all")
        rounded_rect(canvas, 1, 1, w - 1, h - 1, radius=h // 2, fill=state["color"], outline="")
        canvas.create_text(w // 2, h // 2, text=new_text, font=font, fill=fg)

    update(text)
    return canvas, update


def style_button(btn, bg, hover_bg, fg=PALETTE["mantle"], font=None):
    btn.configure(
        bg=bg, fg=fg, activebackground=hover_bg, activeforeground=fg,
        bd=0, relief="flat", font=font or ("Segoe UI", 11, "bold"),
        padx=16, pady=9, cursor="hand2", highlightthickness=0,
    )
    btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.configure(bg=bg))


def make_rounded_card(parent, bg_color, radius=14, shadow=True, stretch_x=False):
    """A drop-in replacement for a plain tk.Frame 'card': a Canvas draws a
    rounded, softly-shadowed background that automatically resizes to fit
    whatever gets packed into the returned inner Frame.

    stretch_x=True makes the card track its parent's available width (for
    full-width list rows where right-aligned buttons need to reach the
    edge); stretch_x=False sizes the card to hug its content instead.

    Usage:
        card, inner = make_rounded_card(parent, PALETTE["surface0"], stretch_x=True)
        card.pack(fill="x", padx=16, pady=5)      # pack the CARD
        tk.Label(inner, ...).pack(...)             # put content in INNER
    """
    parent_bg = parent.cget("bg") if hasattr(parent, "cget") else PALETTE["base"]
    shadow_pad = 5 if shadow else 2

    canvas = tk.Canvas(parent, bg=parent_bg, highlightthickness=0, bd=0)
    inner = tk.Frame(canvas, bg=bg_color)
    window_id = canvas.create_window(shadow_pad, shadow_pad, window=inner, anchor="nw")

    last_size = {"wh": (0, 0)}

    def redraw(_event=None):
        inner.update_idletasks()
        content_w = max(inner.winfo_reqwidth(), 1)
        h = max(inner.winfo_reqheight(), 1)

        if stretch_x:
            canvas_w = canvas.winfo_width()
            w = max(canvas_w - shadow_pad * 2, content_w) if canvas_w > 1 else content_w
        else:
            w = content_w

        if (w, h) == last_size["wh"]:
            return
        last_size["wh"] = (w, h)

        if not stretch_x:
            canvas.config(width=w + shadow_pad * 2)
        canvas.config(height=h + shadow_pad * 2)
        canvas.delete("card_shape")

        if shadow:
            shadow_color = blend_color(bg_color, PALETTE["mantle"], 0.72)
            rounded_rect(
                canvas, shadow_pad - 1, shadow_pad + 2, shadow_pad + w + 1, shadow_pad + h + 4,
                radius, fill=shadow_color, outline="", tags="card_shape",
            )

        rounded_rect(
            canvas, shadow_pad - 2, shadow_pad - 2, shadow_pad + w + 2, shadow_pad + h + 2,
            radius, fill=bg_color, outline="", tags="card_shape",
        )
        canvas.tag_lower("card_shape")
        canvas.coords(window_id, shadow_pad, shadow_pad)
        canvas.itemconfig(window_id, width=w)

    inner.bind("<Configure>", redraw)
    if stretch_x:
        canvas.bind("<Configure>", redraw)
    canvas.after(1, redraw)
    return canvas, inner


class SmoothButton(tk.Canvas):
    """A rounded, drop-shadowed button drawn entirely on a Canvas, with a
    smooth color-interpolated hover transition and a soft press animation —
    tkinter's stock Button has none of this, so it's built from scratch."""

    def __init__(self, parent, text, command=None, bg=PALETTE["accent"],
                 hover_bg=None, fg=PALETTE["mantle"], font=None,
                 padx=16, pady=9, radius=10, shadow=True, **kwargs):
        parent_bg = parent.cget("bg") if hasattr(parent, "cget") else PALETTE["base"]
        super().__init__(parent, highlightthickness=0, bd=0, bg=parent_bg, **kwargs)

        self.text_str = text
        self.command = command
        self.bg_color = bg
        self.hover_color = hover_bg or blend_color(bg, PALETTE["white"], 0.18)
        self.fg_color = fg
        self.font = font or ("Segoe UI", 11, "bold")
        self.radius = radius
        self.shadow = shadow
        self._state = "normal"
        self._current_color = bg
        self._anim_job = None
        self._pressed = False

        tmp = tk.Label(parent, text=text, font=self.font)
        tmp.update_idletasks()
        self._btn_w = tmp.winfo_reqwidth() + padx * 2
        self._btn_h = tmp.winfo_reqheight() + pady * 2
        tmp.destroy()

        shadow_pad = 4 if shadow else 0
        self.configure(width=self._btn_w + shadow_pad, height=self._btn_h + shadow_pad)
        self._shadow_pad = shadow_pad

        self._draw(self.bg_color)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self, color, inset=0):
        self.delete("all")
        if self.shadow and self._state == "normal":
            shadow_color = blend_color(color, PALETTE["mantle"], 0.6)
            rounded_rect(
                self, inset, inset + 2, self._btn_w - inset, self._btn_h - inset + 2,
                self.radius, fill=shadow_color, outline="",
            )
        rounded_rect(self, inset, inset, self._btn_w - inset, self._btn_h - inset, self.radius, fill=color, outline="")
        text_color = self.fg_color if self._state == "normal" else blend_color(self.fg_color, color, 0.55)
        self.create_text((self._btn_w) / 2, (self._btn_h - (4 if self.shadow else 0)) / 2, text=self.text_str,
                          font=self.font, fill=text_color)
        self._current_color = color

    def _animate_to(self, target_color, steps=7, delay=14):
        if self._anim_job:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
        start_color = self._current_color

        def step(i=0):
            t = i / steps
            self._draw(blend_color(start_color, target_color, t))
            if i < steps:
                self._anim_job = self.after(delay, lambda: step(i + 1))
            else:
                self._anim_job = None

        step()

    def _on_enter(self, _event):
        if self._state != "normal":
            return
        self.configure(cursor="hand2")
        self._animate_to(self.hover_color)

    def _on_leave(self, _event):
        if self._state != "normal":
            return
        self.configure(cursor="arrow")
        self._animate_to(self.bg_color)

    def _on_press(self, _event):
        if self._state != "normal":
            return
        self._pressed = True
        self._draw(self.hover_color, inset=2)

    def _on_release(self, event):
        if self._state != "normal":
            self._pressed = False
            return
        was_pressed = self._pressed
        self._pressed = False
        self._draw(self.hover_color)
        if was_pressed and self.command and 0 <= event.x <= self._btn_w and 0 <= event.y <= self._btn_h:
            self.command()

    def config(self, **kwargs):
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            if self._state == "disabled":
                self.configure(cursor="arrow")
                self._draw(blend_color(self.bg_color, PALETTE["mantle"], 0.6))
            else:
                self._draw(self.bg_color)
        if "text" in kwargs:
            self.text_str = kwargs.pop("text")
            self._draw(self._current_color)
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if kwargs:
            super().configure(**kwargs)

    configure = config

    def __getitem__(self, key):
        if key == "state":
            return self._state
        return super().__getitem__(key)


# ---------------------------------------------------------------------------
# Cutscene signature effects — each animation style gets its own drawing
# function so a sword pull looks and moves differently from a ring or a
# crown pull, layered on top of the shared background rings.
# ---------------------------------------------------------------------------

def draw_effect_burst(canvas, cx, cy, f, progress, color, count=20):
    """Default: twinkling particles scattered outward. Used as a fallback
    for any item that doesn't have a more specific style."""
    rng = random.Random(f)
    for _ in range(count):
        angle = rng.uniform(0, 2 * math.pi)
        dist = rng.uniform(20, 150) * min(1.0, progress * 1.3)
        px, py = cx + dist * math.cos(angle), cy + dist * math.sin(angle)
        size = rng.uniform(1.4, 3.4)
        dot_color = color if rng.random() > 0.4 else PALETTE["white"]
        canvas.create_oval(px - size, py - size, px + size, py + size, fill=dot_color, outline="")


def draw_effect_slash(canvas, cx, cy, f, progress, color):
    """Repeating diagonal sword-slash streaks."""
    glow = blend_color(color, PALETTE["white"], 0.45)
    for i in range(2):
        cycle = (f + i * 9) % 22
        if cycle >= 13:
            continue
        t = cycle / 13
        length = 300
        angle = math.radians(-38 if i == 0 else 35)
        dx, dy = math.cos(angle), math.sin(angle)
        spread = (t - 0.5) * 220
        mx, my = cx + (-dy) * spread, cy - 20 + dx * spread
        x1, y1 = mx - dx * length / 2, my - dy * length / 2
        x2, y2 = mx + dx * length / 2, my + dy * length / 2
        width = max(1, 7 * (1 - abs(t - 0.5) * 2))
        canvas.create_line(x1, y1, x2, y2, fill=glow, width=width, capstyle="round")


def draw_effect_starburst(canvas, cx, cy, f, progress, color):
    """Rotating sunburst rays, like a shield catching light."""
    n = 12
    rotation = f * 0.05
    for i in range(n):
        angle = rotation + i * (2 * math.pi / n)
        length = (90 + 14 * math.sin(f * 0.15 + i)) * min(1.0, progress * 1.4)
        x2, y2 = cx + length * math.cos(angle), cy + length * math.sin(angle)
        ray_color = blend_color(color, PALETTE["mantle"], 0.25)
        canvas.create_line(cx, cy, x2, y2, fill=ray_color, width=2)


def draw_effect_halo(canvas, cx, cy, f, progress, color):
    """A rotating ring of small dashes, like a crown's halo."""
    n = 16
    rotation = f * 0.06
    radius = 95 * min(1.0, progress * 1.4)
    for i in range(n):
        angle = rotation + i * (2 * math.pi / n)
        x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        size = 3 if i % 2 == 0 else 2
        dot_color = color if i % 3 else PALETTE["white"]
        canvas.create_oval(x - size, y - size, x + size, y + size, fill=dot_color, outline="")


def draw_effect_pulse(canvas, cx, cy, f, progress, color):
    """A single ring that pulses in and out like a heartbeat/clock tick."""
    beat = (math.sin(f * 0.22) + 1) / 2  # 0..1
    radius = (40 + beat * 45) * min(1.0, progress * 1.4)
    ring_color = blend_color(color, PALETTE["white"], 0.3)
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=ring_color, width=3)
    # a small orbiting tick, like a clock hand sweeping
    hand_angle = f * 0.12
    hx, hy = cx + radius * 0.9 * math.cos(hand_angle), cy + radius * 0.9 * math.sin(hand_angle)
    canvas.create_oval(hx - 3, hy - 3, hx + 3, hy + 3, fill=PALETTE["white"], outline="")


def draw_effect_vortex(canvas, cx, cy, f, progress, color):
    """Particles spiraling inward, like a portal or void pulling matter in."""
    n = 22
    for i in range(n):
        angle = f * 0.1 + i * (2 * math.pi / n)
        dist = 150 - ((f * 2 + i * 7) % 150)
        x, y = cx + dist * math.cos(angle), cy + dist * math.sin(angle)
        size = 1.4 + (150 - dist) / 150 * 2.6
        dot_color = blend_color(color, PALETTE["white"], (150 - dist) / 180)
        canvas.create_oval(x - size, y - size, x + size, y + size, fill=dot_color, outline="")


def draw_effect_orbit(canvas, cx, cy, f, progress, color):
    """A few dots orbiting the center at different radii/speeds."""
    for ring in range(3):
        radius = (36 + ring * 32) * min(1.0, progress * 1.4)
        speed = 0.09 - ring * 0.02
        angle = f * speed + ring * 2.1
        x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        size = 4 - ring * 0.6
        dot_color = blend_color(color, PALETTE["white"], 0.25)
        canvas.create_oval(x - size, y - size, x + size, y + size, fill=dot_color, outline="")


def draw_effect_divine(canvas, cx, cy, f, progress, color):
    """The most elaborate effect: rays plus orbiting sparks plus a slow
    breathing halo — reserved for the rarest Godlike items."""
    draw_effect_starburst(canvas, cx, cy, f, progress, color)
    draw_effect_orbit(canvas, cx, cy, f, progress, color)
    beat = (math.sin(f * 0.1) + 1) / 2
    radius = (70 + beat * 20) * min(1.0, progress * 1.4)
    ring_color = blend_color(color, PALETTE["white"], 0.5)
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=ring_color, width=2)


STYLE_EFFECTS = {
    "slash": draw_effect_slash,
    "starburst": draw_effect_starburst,
    "halo": draw_effect_halo,
    "pulse": draw_effect_pulse,
    "vortex": draw_effect_vortex,
    "orbit": draw_effect_orbit,
    "divine": draw_effect_divine,
}


def make_progress_bar(parent, width, height, progress, fg_color, bg_color=None):
    """A small rounded progress bar (0.0-1.0), drawn on a Canvas since
    ttk's stock progress bar doesn't support rounded corners or theming."""
    bg_color = bg_color or PALETTE["surface1"]
    parent_bg = parent.cget("bg") if hasattr(parent, "cget") else PALETTE["base"]
    canvas = tk.Canvas(parent, width=width, height=height, bg=parent_bg, highlightthickness=0, bd=0)
    rounded_rect(canvas, 0, 0, width, height, height / 2, fill=bg_color, outline="")
    progress = max(0.0, min(1.0, progress))
    if progress > 0:
        fill_w = max(height, width * progress)
        rounded_rect(canvas, 0, 0, fill_w, height, height / 2, fill=fg_color, outline="")
    return canvas


class RNGGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✦ RNG Item Roller")
        self.root.configure(bg=PALETTE["mantle"])
        self.root.resizable(True, True)
        self.root.minsize(720, 560)
        self._is_fullscreen = False
        self._start_maximized()
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)

        self.currency = STARTING_CURRENCY
        self.total_rolls = 0
        self.inventory = {rarity: Counter() for rarity in RARITIES}
        self.rarity_counts = Counter()

        self.active_boosts = []          # list of dicts: name, multiplier, affected, rolls_remaining, boost_pct, scope
        self.permanent_boosts = []       # crafted gear effects - same shape but never expire
        self.craft_materials = Counter() # rarity -> quantity reserved for crafting (not sellable)
        self.crafted_gear = []           # list of completed recipe dicts
        self.active_recipe = None        # recipe currently receiving auto-crafted materials
        self.auto_craft_var = tk.BooleanVar(value=True)
        self._cutscene_queue = []
        self.shop_time_left = SHOP_REFRESH_SECONDS
        self.shop_items = []
        self._generate_shop_items()

        # Index / lifetime tracking — separate from self.inventory, which
        # only reflects what you currently hold. These never decrease,
        # even after selling or crafting something away.
        self.lifetime_counts = Counter()      # rarity -> total ever rolled
        self.lifetime_item_counts = Counter() # item name -> total ever rolled
        self.first_discovered = {}            # item name -> roll # it was first found on
        self.completed_achievements = set()   # achievement names already paid out
        self.redeemed_codes = set()           # codes already used

        # Biomes — a free, passive luck effect that rotates on its own
        # timer, independent of anything the player buys or crafts.
        self.current_biome = BIOMES[0]
        self.biome_time_left = BIOME_ROTATE_SECONDS

        # Minesweeper minigame state (None until a game is started)
        self.mine_game = None

        self._configure_ttk_style()
        self._build_status_bar()
        self._build_notebook()

        self.refresh_collection_tab()
        self.refresh_sell_tab()

        self.root.after(1000, self._shop_tick)
        self.root.after(1000, self._biome_tick)

    # ------------------------------------------------------------------
    # STYLE / THEME SETUP
    # ------------------------------------------------------------------
    def _start_maximized(self):
        """Open filling the screen. Different OS/window managers expose
        this differently, so try each approach in turn."""
        try:
            self.root.state("zoomed")  # Windows, and some Linux window managers
            return
        except tk.TclError:
            pass
        try:
            self.root.attributes("-zoomed", True)  # most Linux window managers
            return
        except tk.TclError:
            pass
        self.root.update_idletasks()
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+0+0")

    def _toggle_fullscreen(self, _event=None):
        self._is_fullscreen = not self._is_fullscreen
        self.root.attributes("-fullscreen", self._is_fullscreen)

    def _exit_fullscreen(self, _event=None):
        if self._is_fullscreen:
            self._is_fullscreen = False
            self.root.attributes("-fullscreen", False)

    def _configure_ttk_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=PALETTE["base"])
        style.configure("TLabel", background=PALETTE["base"], foreground=PALETTE["text"])

        style.configure(
            "TNotebook", background=PALETTE["mantle"], borderwidth=0, tabmargins=[10, 10, 10, 0]
        )
        style.configure(
            "TNotebook.Tab", background=PALETTE["surface0"], foreground=PALETTE["subtext"],
            padding=[20, 12], font=("Segoe UI", 11, "bold"), borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", PALETTE["accent"])],
            foreground=[("selected", PALETTE["mantle"])],
        )

        style.configure(
            "Vertical.TScrollbar", background=PALETTE["surface1"],
            troughcolor=PALETTE["base"], bordercolor=PALETTE["base"],
            arrowcolor=PALETTE["text"], relief="flat",
        )

    # ------------------------------------------------------------------
    # STATUS BAR
    # ------------------------------------------------------------------
    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=PALETTE["mantle"], padx=16, pady=12)
        bar.pack(fill="x")

        tk.Label(
            bar, text="✦ RNG Item Roller", font=FONT_TITLE,
            bg=PALETTE["mantle"], fg=PALETTE["text"],
        ).pack(side="left")

        stats = tk.Frame(bar, bg=PALETTE["mantle"])
        stats.pack(side="right")

        self.coin_pill, self._coin_pill_update = make_dynamic_badge(stats, f"💰 {self.currency}", PALETTE["yellow"])
        self.coin_pill.pack(side="right", padx=(10, 0))

        self.rolls_pill, self._rolls_pill_update = make_dynamic_badge(
            stats, f"🎲 {self.total_rolls} rolls", PALETTE["surface2"], fg=PALETTE["text"]
        )
        self.rolls_pill.pack(side="right")
        self._currency_display = self.currency

    # ------------------------------------------------------------------
    # NOTEBOOK / TABS
    # ------------------------------------------------------------------
    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.roll_tab = tk.Frame(self.notebook, bg=PALETTE["base"])
        self.collection_tab = tk.Frame(self.notebook, bg=PALETTE["base"])
        self.sell_tab = tk.Frame(self.notebook, bg=PALETTE["base"])
        self.shop_tab = tk.Frame(self.notebook, bg=PALETTE["base"])
        self.craft_tab = tk.Frame(self.notebook, bg=PALETTE["base"])
        self.index_tab = tk.Frame(self.notebook, bg=PALETTE["base"])
        self.mine_tab = tk.Frame(self.notebook, bg=PALETTE["base"])
        self.odds_tab = tk.Frame(self.notebook, bg=PALETTE["base"])

        self.notebook.add(self.roll_tab, text="  🎲 Roll  ")
        self.notebook.add(self.collection_tab, text="  📦 Collection  ")
        self.notebook.add(self.sell_tab, text="  💰 Sell  ")
        self.notebook.add(self.shop_tab, text="  🛒 Shop  ")
        self.notebook.add(self.craft_tab, text="  ⚒ Craft  ")
        self.notebook.add(self.index_tab, text="  📖 Index  ")
        self.notebook.add(self.mine_tab, text="  🎮 Minigame  ")
        self.notebook.add(self.odds_tab, text="  📊 Odds  ")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Ctrl+Tab / Ctrl+Shift+Tab cycles tabs (ttk's built-in traversal);
        # Ctrl+1..8 jumps straight to a tab, like browser tabs.
        self.notebook.enable_traversal()
        for i in range(8):
            self.root.bind(f"<Control-Key-{i + 1}>", lambda e, idx=i: self.notebook.select(idx))

        self._build_roll_tab()
        self._build_odds_tab()
        self.refresh_shop_tab()
        self.refresh_craft_tab()
        self.refresh_index_tab()
        self.refresh_mine_tab()
        self._refresh_boosts_strip()

    def _on_tab_changed(self, event):
        tab_text = event.widget.tab(event.widget.select(), "text").strip()
        if "Collection" in tab_text:
            self.refresh_collection_tab()
        elif "Sell" in tab_text:
            self.refresh_sell_tab()
        elif "Shop" in tab_text:
            self.refresh_shop_tab()
        elif "Craft" in tab_text:
            self.refresh_craft_tab()
        elif "Index" in tab_text:
            self.refresh_index_tab()
        elif "Minigame" in tab_text:
            self.refresh_mine_tab()

    # ------------------------------------------------------------------
    # ROLL TAB
    # ------------------------------------------------------------------
    def _build_roll_tab(self):
        frame = self.roll_tab

        # Biome banner — a free, passive effect that rotates on its own,
        # independent of anything bought or crafted.
        biome_row = tk.Frame(frame, bg=PALETTE["base"])
        biome_row.pack(fill="x", padx=20, pady=(14, 0))
        self.biome_pill, self.biome_label_update = make_dynamic_badge(
            biome_row, "🌎 Loading biome…", PALETTE["subtext"]
        )
        self.biome_pill.pack(anchor="w")
        self._update_biome_banner()

        # Result card, with a soft ambient glow layered behind it that
        # recolors to match whatever rarity was just rolled.
        glow_wrap = tk.Frame(frame, bg=PALETTE["base"])
        glow_wrap.pack(fill="x", padx=20, pady=(14, 14))

        self.glow_canvas = tk.Canvas(glow_wrap, height=180, bg=PALETTE["base"], highlightthickness=0, bd=0)
        self.glow_canvas.pack(fill="both", expand=True)
        self._glow_color = PALETTE["accent"]
        self.glow_canvas.bind("<Configure>", lambda e: self._draw_ambient_glow(self._glow_color))

        self.result_card, result_body = make_rounded_card(glow_wrap, PALETTE["surface0"])
        self.result_card.place(in_=glow_wrap, relx=0.5, rely=0.5, anchor="center")

        result_pad = tk.Frame(result_body, bg=PALETTE["surface0"], padx=28, pady=24)
        result_pad.pack()

        self.badge_holder = tk.Frame(result_pad, bg=PALETTE["surface0"])
        self.badge_holder.pack()

        self.result_var = tk.StringVar(value="Press Roll to try your luck")
        self.result_label = tk.Label(
            result_pad, textvariable=self.result_var, font=("Segoe UI", 17, "bold"),
            bg=PALETTE["surface0"], fg=PALETTE["text"], pady=14, wraplength=460,
        )
        self.result_label.pack()

        # Active boosts strip
        self.boosts_strip = tk.Frame(frame, bg=PALETTE["base"])
        self.boosts_strip.pack(fill="x", padx=20, pady=(0, 6))

        # Buttons
        btn_frame = tk.Frame(frame, bg=PALETTE["base"])
        btn_frame.pack(pady=(0, 14))

        self.roll_btn = SmoothButton(
            btn_frame, f"Roll  ·  −{ROLL_COST} coin", command=self.do_single_roll,
            bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], radius=12,
        )
        self.roll_btn.grid(row=0, column=0, padx=6)

        self.roll10_btn = SmoothButton(
            btn_frame, f"Roll ×10  ·  −{ROLL_COST * 10} coins", command=self.do_ten_roll,
            bg=PALETTE["peach"], hover_bg="#f8a978", radius=12,
        )
        self.roll10_btn.grid(row=0, column=1, padx=6)

        # Log
        tk.Label(
            frame, text="RECENT ROLLS", font=("Segoe UI", 9, "bold"),
            bg=PALETTE["base"], fg=PALETTE["subtext"],
        ).pack(anchor="w", padx=22)

        log_wrap = tk.Frame(frame, bg=PALETTE["surface0"])
        log_wrap.pack(fill="both", expand=True, padx=20, pady=(4, 20))

        self.last_log = tk.Text(
            log_wrap, height=10, bg=PALETTE["surface0"], fg=PALETTE["text"],
            font=FONT_MONO, bd=0, highlightthickness=0, padx=14, pady=10,
            state="disabled", wrap="word",
        )
        self.last_log.pack(fill="both", expand=True)

        for rarity, info in RARITIES.items():
            self.last_log.tag_config(rarity, foreground=info["color"])

    def do_single_roll(self):
        self._perform_rolls(1)

    def do_ten_roll(self):
        self._perform_rolls(10)

    def _perform_rolls(self, count):
        cost = ROLL_COST * count
        if self.currency < cost:
            messagebox.showwarning("Not enough coins", "You don't have enough coins to roll!")
            return

        self.currency -= cost
        results = []
        for _ in range(count):
            rarity, item = self._roll_with_boosts()
            diverted = self._maybe_divert_to_crafting(rarity)
            if not diverted:
                self.inventory[rarity][item] += 1
                self.rarity_counts[rarity] += 1
            self.total_rolls += 1
            self.lifetime_counts[rarity] += 1
            self.lifetime_item_counts[item] += 1
            if item not in self.first_discovered:
                self.first_discovered[item] = self.total_rolls
            results.append((rarity, item, diverted))
            self._tick_boosts()

        self._update_status_bar()
        self._refresh_boosts_strip()
        self.refresh_craft_tab()
        self._check_achievements()
        self._start_spin_animation(results)

    def _maybe_divert_to_crafting(self, rarity):
        """If Auto-Craft is on and this rarity is still needed for the
        active recipe, absorb it as a material instead of adding it to the
        sellable collection. Returns True if the item was diverted."""
        if not self.auto_craft_var.get() or not self.active_recipe:
            return False
        needed = self.active_recipe["materials"].get(rarity)
        if needed is None or self.craft_materials[rarity] >= needed:
            return False
        self.craft_materials[rarity] += 1
        return True

    def _roll_with_boosts(self):
        """Weighted rarity roll that applies any currently active potion
        boosts, permanent crafted gear, AND the current biome, then picks
        a random item from that rarity's pool."""
        tiers = list(RARITIES.keys())
        weights = []
        biome_scope = self.current_biome.get("scope")
        for tier in tiers:
            w = RARITIES[tier]["weight"]
            for boost in self.active_boosts:
                if tier in boost["affected"]:
                    w *= boost["multiplier"]
            for boost in self.permanent_boosts:
                if boost.get("kind") == "luck" and tier in boost["affected"]:
                    w *= boost["multiplier"]
            if biome_scope and tier in SCOPE_RARITIES.get(biome_scope, []):
                w *= 1 + self.current_biome["boost_pct"] / 100
            weights.append(w)
        rarity = random.choices(tiers, weights=weights, k=1)[0]
        item = random.choice(ITEM_POOL[rarity])
        return rarity, item

    def _tick_boosts(self):
        """Consume one roll's worth of charge from each active boost,
        dropping any that have run out."""
        still_active = []
        for boost in self.active_boosts:
            boost["rolls_remaining"] -= 1
            if boost["rolls_remaining"] > 0:
                still_active.append(boost)
        self.active_boosts = still_active

    def _start_spin_animation(self, results):
        """Flicker through random items, gradually slowing down, before
        landing on the actual (already-determined) result."""
        self._set_buttons_enabled(False)
        self._spin_results = results
        self._spin_step = 0
        self._spin_total_steps = 16
        self._spin_frame()

    def _spin_frame(self):
        if self._spin_step < self._spin_total_steps:
            flicker_rarity = weighted_rarity_choice()
            flicker_item = random.choice(ITEM_POOL[flicker_rarity])
            self._show_in_card(flicker_rarity, flicker_item)

            self._spin_step += 1
            # Ease out: each frame takes a little longer than the last,
            # so the spin visibly slows down before it lands.
            progress = self._spin_step / self._spin_total_steps
            delay = int(35 + (progress ** 2) * 160)
            self.root.after(delay, self._spin_frame)
        else:
            self._finish_spin_animation()

    def _finish_spin_animation(self):
        results = self._spin_results
        last_rarity, last_item, _ = results[-1]
        self._show_in_card(last_rarity, last_item)
        self._pop_effect()

        self.last_log.config(state="normal")
        for rarity, item, diverted in results:
            self.last_log.insert("end", f"[{rarity}] ", rarity)
            if diverted:
                self.last_log.insert("end", f"{item} ⚒ sent to crafting\n")
            else:
                self.last_log.insert("end", f"{item}\n")
        self.last_log.see("end")
        self.last_log.config(state="disabled")

        self.refresh_collection_tab()
        self.refresh_sell_tab()

        # Any Super Rare-and-up pulls get a dedicated cutscene, played in
        # sequence. Buttons stay locked until the whole queue finishes.
        cutscene_pulls = [(r, i) for r, i, _ in results if r in CUTSCENE_CONFIG]
        if cutscene_pulls:
            self._cutscene_queue = cutscene_pulls
            self._play_next_cutscene()
        else:
            self._set_buttons_enabled(True)

    def _show_in_card(self, rarity, item_name):
        color = RARITIES[rarity]["color"]
        for widget in self.badge_holder.winfo_children():
            widget.destroy()
        badge = make_badge(self.badge_holder, rarity.upper(), color, PALETTE["surface0"])
        badge.pack()
        self.result_var.set(item_name)
        self.result_label.config(fg=color)
        self._draw_ambient_glow(color)

    def _draw_ambient_glow(self, color):
        """A soft, blurred-looking halo of concentric ovals behind the
        result card, color-matched to whatever was just rolled. tkinter
        has no real blur, so this fakes it with fading nested shapes."""
        if not hasattr(self, "glow_canvas"):
            return
        self._glow_color = color
        canvas = self.glow_canvas
        w = max(canvas.winfo_width(), 480)
        h = max(canvas.winfo_height(), 180)
        cx, cy = w // 2, h // 2
        canvas.delete("glow")
        for i in range(6, 0, -1):
            rx, ry = i * 42, i * 20
            t = i / 6
            ring_color = blend_color(color, PALETTE["base"], 0.25 + t * 0.6)
            canvas.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, fill=ring_color, outline="", tags="glow")
        canvas.tag_lower("glow")

    def _pop_effect(self):
        """Brief scale-up 'pop' on the final result so it feels like it lands."""
        self.result_label.config(font=("Segoe UI", 21, "bold"))
        self.root.after(140, lambda: self.result_label.config(font=("Segoe UI", 17, "bold")))

    # ------------------------------------------------------------------
    # CUTSCENES (Super Rare and up)
    # ------------------------------------------------------------------
    def _play_next_cutscene(self):
        if not self._cutscene_queue:
            self._set_buttons_enabled(True)
            return
        rarity, item = self._cutscene_queue.pop(0)
        self._show_cutscene(rarity, item, on_done=self._play_next_cutscene)

    def _show_cutscene(self, rarity, item_name, on_done):
        config = CUTSCENE_CONFIG[rarity]
        color = RARITIES[rarity]["color"]
        width, height = 480, 340

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - height) // 2

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.geometry(f"{width}x{height}+{x}+{y}")
        win.configure(bg=PALETTE["mantle"])
        win.attributes("-topmost", True)

        canvas = tk.Canvas(win, width=width, height=height, bg=PALETTE["mantle"], highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        cx, cy = width // 2, height // 2 - 10

        state = {"frame": 0, "closed": False, "timer_id": None}
        # Run the animation loop for (almost) the whole time the cutscene
        # is on screen, so longer cutscenes stay dynamic instead of
        # freezing on a static frame while they wait to auto-close.
        frame_delay = 45
        total_frames = max(30, config["hold_ms"] // frame_delay - 4)
        effect_fn = STYLE_EFFECTS.get(ITEM_ANIMATION_STYLE.get(item_name))

        def close(_event=None):
            if state["closed"]:
                return
            state["closed"] = True
            if state["timer_id"]:
                try:
                    win.after_cancel(state["timer_id"])
                except Exception:
                    pass
            try:
                win.grab_release()
            except Exception:
                pass
            win.destroy()
            on_done()

        win.bind("<Button-1>", close)
        win.bind("<Key>", close)
        win.grab_set()
        win.focus_force()

        def animate():
            if state["closed"]:
                return
            canvas.delete("all")
            f = state["frame"]
            progress = min(1.0, f / total_frames)

            # Expanding burst rings that fade toward the background color
            for i in range(config["rings"]):
                ring_progress = max(0.0, min(1.0, progress * 1.4 - i * 0.14))
                if ring_progress <= 0:
                    continue
                radius = ring_progress * (120 + i * 16)
                ring_color = blend_color(color, PALETTE["mantle"], 0.3 + 0.55 * ring_progress)
                canvas.create_oval(
                    cx - radius, cy - radius, cx + radius, cy + radius,
                    outline=ring_color, width=2,
                )

            # Item-specific signature effect (falls back to the generic
            # twinkling burst if this item has no dedicated style)
            if effect_fn:
                effect_fn(canvas, cx, cy, f, progress, color)
            else:
                draw_effect_burst(canvas, cx, cy, f, progress, color, count=config["particles"])

            # Rarity title scales in
            title_progress = min(1.0, max(0.0, (f - 3) / 12))
            if title_progress > 0:
                size = int(12 + title_progress * (config["title_size"] - 12))
                canvas.create_text(
                    cx, cy - 26, text=config["title"], font=("Segoe UI", size, "bold"), fill=color,
                )

            # Item name fades in a little after the title
            if f > 15:
                canvas.create_text(
                    cx, cy + 34, text=item_name, font=("Segoe UI", 15, "bold"), fill=PALETTE["text"],
                )

            if f > 20:
                canvas.create_text(
                    cx, height - 22, text="click to continue",
                    font=("Segoe UI", 9), fill=PALETTE["subtext"],
                )

            state["frame"] += 1
            if state["frame"] <= total_frames:
                win.after(frame_delay, animate)

        animate()
        state["timer_id"] = win.after(config["hold_ms"], close)

    def _refresh_boosts_strip(self):
        for widget in self.boosts_strip.winfo_children():
            widget.destroy()

        if not self.active_boosts and not self.permanent_boosts:
            return

        if self.active_boosts:
            tk.Label(
                self.boosts_strip, text="ACTIVE BOOSTS", font=("Segoe UI", 8, "bold"),
                bg=PALETTE["base"], fg=PALETTE["subtext"],
            ).pack(anchor="w")

            row = tk.Frame(self.boosts_strip, bg=PALETTE["base"])
            row.pack(anchor="w", pady=(2, 6))

            for boost in self.active_boosts:
                rep_color = RARITIES[boost["affected"][0]]["color"]
                chip = make_badge(
                    row, f"{boost['name']} +{boost['boost_pct']}%  ({boost['rolls_remaining']})",
                    rep_color, PALETTE["base"],
                )
                chip.pack(side="left", padx=(0, 6))

        if self.permanent_boosts:
            tk.Label(
                self.boosts_strip, text="EQUIPPED GEAR", font=("Segoe UI", 8, "bold"),
                bg=PALETTE["base"], fg=PALETTE["subtext"],
            ).pack(anchor="w")

            row = tk.Frame(self.boosts_strip, bg=PALETTE["base"])
            row.pack(anchor="w", pady=(2, 0))

            for boost in self.permanent_boosts:
                if boost["kind"] == "luck":
                    rep_color = RARITIES[boost["affected"][0]]["color"]
                    label = f"{boost['name']} +{boost['boost_pct']}%  ∞"
                else:
                    rep_color = PALETTE["yellow"]
                    label = f"{boost['name']} +{boost['pct']}% coins  ∞"
                chip = make_badge(row, label, rep_color, PALETTE["base"])
                chip.pack(side="left", padx=(0, 6))

    def _set_buttons_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        cursor = "hand2" if enabled else "arrow"
        self.roll_btn.config(state=state, cursor=cursor)
        self.roll10_btn.config(state=state, cursor=cursor)

    # ------------------------------------------------------------------
    # COLLECTION TAB
    # ------------------------------------------------------------------
    def refresh_collection_tab(self):
        self._rebuild_scrollable(self.collection_tab, self._populate_collection)

    def _populate_collection(self, scroll_frame):
        has_items = any(self.inventory[r] for r in RARITIES)
        if not has_items:
            tk.Label(
                scroll_frame, text="You haven't rolled anything yet.",
                font=FONT_BODY, bg=PALETTE["base"], fg=PALETTE["subtext"], pady=20,
            ).pack()
            return

        for rarity in RARITIES:
            items = self.inventory[rarity]
            if not items:
                continue
            color = RARITIES[rarity]["color"]

            section = tk.Frame(scroll_frame, bg=PALETTE["base"])
            section.pack(fill="x", padx=16, pady=(14, 4))
            badge = make_badge(section, f"{rarity}  ({self.rarity_counts[rarity]})", color, PALETTE["base"])
            badge.pack(anchor="w")

            for item, cnt in items.items():
                self._make_item_card(scroll_frame, item, cnt, color)

    def _make_item_card(self, parent, item_name, count, color, extra=None):
        card, body = make_rounded_card(parent, PALETTE["surface0"], stretch_x=True)
        card.pack(fill="x", padx=16, pady=4)

        row = tk.Frame(body, bg=PALETTE["surface0"])
        row.pack(fill="both", expand=True)

        stripe_canvas = tk.Canvas(row, width=4, bg=PALETTE["surface0"], highlightthickness=0, bd=0)
        stripe_canvas.pack(side="left", fill="y")
        stripe_canvas.bind(
            "<Configure>",
            lambda e, c=stripe_canvas, col=color: (
                c.delete("all"),
                c.create_rectangle(0, 4, 4, e.height - 4, fill=col, outline=""),
            ),
        )

        content = tk.Frame(row, bg=PALETTE["surface0"])
        content.pack(side="left", fill="both", expand=True, padx=12, pady=9)

        tk.Label(
            content, text=f"{item_name}", font=FONT_BODY,
            bg=PALETTE["surface0"], fg=PALETTE["text"], anchor="w",
        ).pack(side="left")

        tk.Label(
            content, text=f"×{count}", font=("Segoe UI", 10, "bold"),
            bg=PALETTE["surface0"], fg=PALETTE["subtext"],
        ).pack(side="left", padx=(8, 0))

        if extra:
            extra(row)

        return card

    # ------------------------------------------------------------------
    # SELL TAB
    # ------------------------------------------------------------------
    def refresh_sell_tab(self):
        self._rebuild_scrollable(self.sell_tab, self._populate_sell, top_bar_fn=self._build_sell_top_bar)

    def _populate_sell(self, scroll_frame):
        has_items = any(self.inventory[r] for r in RARITIES)
        if not has_items:
            tk.Label(
                scroll_frame, text="Nothing to sell yet — go roll something!",
                font=FONT_BODY, bg=PALETTE["base"], fg=PALETTE["subtext"], pady=20,
            ).pack()
            return

        for rarity in RARITIES:
            items = self.inventory[rarity]
            if not items:
                continue
            color = RARITIES[rarity]["color"]
            value = RARITIES[rarity]["sell_value"]

            section = tk.Frame(scroll_frame, bg=PALETTE["base"])
            section.pack(fill="x", padx=16, pady=(14, 4))
            badge = make_badge(section, f"{rarity}  ·  {value}c each", color, PALETTE["base"])
            badge.pack(anchor="w")

            for item, cnt in list(items.items()):
                def add_sell_buttons(row_frame, r=rarity, i=item, c=cnt):
                    btn_wrap = tk.Frame(row_frame, bg=PALETTE["surface0"])
                    btn_wrap.pack(side="right", padx=10)

                    b1 = SmoothButton(
                        btn_wrap, "Sell 1", command=lambda: self.sell_item(r, i, 1),
                        bg=PALETTE["surface2"], hover_bg=PALETTE["surface1"], fg=PALETTE["text"],
                        font=FONT_SMALL, padx=10, pady=5, radius=8, shadow=False,
                    )
                    b1.pack(side="left", padx=3)

                    b2 = SmoothButton(
                        btn_wrap, "Sell All", command=lambda: self.sell_item(r, i, c),
                        bg=color, hover_bg=blend_color(color, PALETTE["white"], 0.2), fg=PALETTE["mantle"],
                        font=FONT_SMALL, padx=10, pady=5, radius=8, shadow=False,
                    )
                    b2.pack(side="left", padx=3)

                self._make_item_card(scroll_frame, item, cnt, color, extra=add_sell_buttons)

    def _build_sell_top_bar(self, parent):
        bar = tk.Frame(parent, bg=PALETTE["base"], pady=8, padx=16)
        bar.pack(fill="x")
        btn = SmoothButton(
            bar, "Sell Everything", command=self.sell_everything,
            bg=PALETTE["red"], hover_bg="#f5849e", fg=PALETTE["mantle"], radius=10,
        )
        btn.pack(side="right")

    def _sell_multiplier(self):
        multiplier = 1.0
        for boost in self.permanent_boosts:
            if boost["kind"] == "sell_bonus":
                multiplier += boost["pct"] / 100
        return multiplier

    def sell_item(self, rarity, item, quantity):
        available = self.inventory[rarity][item]
        quantity = min(quantity, available)
        if quantity <= 0:
            return

        value = int(round(RARITIES[rarity]["sell_value"] * quantity * self._sell_multiplier()))
        self.inventory[rarity][item] -= quantity
        if self.inventory[rarity][item] <= 0:
            del self.inventory[rarity][item]
        self.rarity_counts[rarity] -= quantity
        self.currency += value

        self._update_status_bar()
        self.refresh_sell_tab()
        self.refresh_collection_tab()

    def sell_everything(self):
        has_items = any(self.inventory[r] for r in RARITIES)
        if not has_items:
            return
        if not messagebox.askyesno("Confirm", "Sell your entire collection?"):
            return

        multiplier = self._sell_multiplier()
        total = 0
        for rarity in RARITIES:
            for item, cnt in list(self.inventory[rarity].items()):
                total += int(round(RARITIES[rarity]["sell_value"] * cnt * multiplier))
                self.rarity_counts[rarity] -= cnt
                del self.inventory[rarity][item]

        self.currency += total
        self._update_status_bar()
        self.refresh_sell_tab()
        self.refresh_collection_tab()
        messagebox.showinfo("Sold!", f"Sold your whole collection for {total} coins!")

    # ------------------------------------------------------------------
    # SHOP TAB
    # ------------------------------------------------------------------
    def _generate_shop_items(self):
        chosen = random.sample(POTION_CATALOG, k=min(SHOP_SLOT_COUNT, len(POTION_CATALOG)))
        items = []
        for template in chosen:
            boost = random.randint(*template["boost_range"])
            duration = random.randint(*template["duration_range"])
            price = int(round(template["base_price"] * random.uniform(0.85, 1.25)))
            items.append({
                "name": template["name"],
                "scope": template["scope"],
                "boost": boost,
                "duration": duration,
                "price": price,
            })
        self.shop_items = items

    def refresh_shop_tab(self):
        self._rebuild_scrollable(self.shop_tab, self._populate_shop, top_bar_fn=self._build_shop_top_bar)

    def _build_shop_top_bar(self, parent):
        header = tk.Frame(parent, bg=PALETTE["base"], padx=16, pady=12)
        header.pack(fill="x")

        tk.Label(
            header, text="Shop", font=FONT_HEADER,
            bg=PALETTE["base"], fg=PALETTE["text"],
        ).pack(side="left")

        self.shop_timer_label = tk.Label(
            header, text="", font=FONT_BODY,
            bg=PALETTE["base"], fg=PALETTE["subtext"],
        )
        self.shop_timer_label.pack(side="right")
        self._update_shop_timer_label()

        tk.Label(
            parent,
            text="Potions temporarily boost the odds of rolling higher rarities.",
            font=FONT_SMALL, bg=PALETTE["base"], fg=PALETTE["subtext"],
        ).pack(anchor="w", padx=16, pady=(0, 8))

        redeem_card, redeem_body = make_rounded_card(parent, PALETTE["surface0"], stretch_x=True)
        redeem_card.pack(fill="x", padx=16, pady=(0, 12))
        redeem_row = tk.Frame(redeem_body, bg=PALETTE["surface0"], padx=12, pady=10)
        redeem_row.pack(fill="x")

        tk.Label(
            redeem_row, text="Redeem Code", font=("Segoe UI", 10, "bold"),
            bg=PALETTE["surface0"], fg=PALETTE["text"],
        ).pack(side="left")

        self.redeem_entry = tk.Entry(
            redeem_row, font=FONT_SMALL, bg=PALETTE["surface1"], fg=PALETTE["text"],
            insertbackground=PALETTE["text"], relief="flat", width=16,
        )
        self.redeem_entry.pack(side="left", padx=(10, 6), ipady=4)
        self.redeem_entry.bind("<Return>", lambda e: self.redeem_code())

        redeem_btn = SmoothButton(
            redeem_row, "Redeem", command=self.redeem_code,
            bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], fg=PALETTE["mantle"],
            font=FONT_SMALL, padx=12, pady=5, radius=8, shadow=False,
        )
        redeem_btn.pack(side="left")

    def redeem_code(self):
        code = self.redeem_entry.get().strip().upper()
        self.redeem_entry.delete(0, "end")
        if not code:
            return
        if code in self.redeemed_codes:
            messagebox.showwarning("Already used", "That code has already been redeemed.")
            return
        reward = REDEEM_CODES.get(code)
        if not reward:
            messagebox.showwarning("Invalid code", f'"{code}" isn\'t a valid code.')
            return
        self.redeemed_codes.add(code)
        self.currency += reward.get("coins", 0)
        self._update_status_bar()
        messagebox.showinfo("Code redeemed!", f"+{reward.get('coins', 0)} coins")

    def _populate_shop(self, scroll_frame):
        for item in self.shop_items:
            self._make_shop_card(scroll_frame, item)

    def _make_shop_card(self, parent, item):
        affected = SCOPE_RARITIES[item["scope"]]
        color = RARITIES[affected[0]]["color"]

        card, body = make_rounded_card(parent, PALETTE["surface0"], stretch_x=True)
        card.pack(fill="x", padx=16, pady=5)

        row = tk.Frame(body, bg=PALETTE["surface0"])
        row.pack(fill="both", expand=True)

        stripe_canvas = tk.Canvas(row, width=4, bg=PALETTE["surface0"], highlightthickness=0, bd=0)
        stripe_canvas.pack(side="left", fill="y")
        stripe_canvas.bind(
            "<Configure>",
            lambda e, c=stripe_canvas, col=color: (
                c.delete("all"),
                c.create_rectangle(0, 4, 4, e.height - 4, fill=col, outline=""),
            ),
        )

        inner = tk.Frame(row, bg=PALETTE["surface0"], padx=14, pady=10)
        inner.pack(side="left", fill="both", expand=True)

        top_row = tk.Frame(inner, bg=PALETTE["surface0"])
        top_row.pack(fill="x")

        tk.Label(
            top_row, text=item["name"], font=("Segoe UI", 12, "bold"),
            bg=PALETTE["surface0"], fg=PALETTE["text"], anchor="w",
        ).pack(side="left")

        tk.Label(
            top_row, text=f"💰 {item['price']}", font=("Segoe UI", 11, "bold"),
            bg=PALETTE["surface0"], fg=PALETTE["yellow"],
        ).pack(side="right")

        tk.Label(
            inner, text=f"Boosts {item['scope']} odds by +{item['boost']}%  ·  lasts {item['duration']} rolls",
            font=FONT_SMALL, bg=PALETTE["surface0"], fg=PALETTE["subtext"], anchor="w",
        ).pack(fill="x", pady=(4, 8))

        buy_btn = SmoothButton(
            inner, "Buy", command=lambda i=item: self.buy_potion(i),
            bg=color, hover_bg=blend_color(color, PALETTE["white"], 0.2), fg=PALETTE["mantle"],
            font=FONT_SMALL, padx=14, pady=6, radius=9, shadow=False,
        )
        buy_btn.pack(anchor="e")

    def buy_potion(self, item):
        if self.currency < item["price"]:
            messagebox.showwarning("Not enough coins", "You can't afford this potion yet!")
            return

        self.currency -= item["price"]
        self.active_boosts.append({
            "name": item["name"],
            "scope": item["scope"],
            "affected": SCOPE_RARITIES[item["scope"]],
            "multiplier": 1 + item["boost"] / 100,
            "boost_pct": item["boost"],
            "rolls_remaining": item["duration"],
        })

        self._update_status_bar()
        self._refresh_boosts_strip()
        messagebox.showinfo(
            "Potion purchased!",
            f"{item['name']} activated — +{item['boost']}% to {item['scope']} odds for {item['duration']} rolls.",
        )

    def _shop_tick(self):
        self.shop_time_left -= 1
        if self.shop_time_left <= 0:
            self._generate_shop_items()
            self.shop_time_left = SHOP_REFRESH_SECONDS
            self.refresh_shop_tab()
        else:
            self._update_shop_timer_label()
        self.root.after(1000, self._shop_tick)

    def _update_shop_timer_label(self):
        if not hasattr(self, "shop_timer_label"):
            return
        minutes, seconds = divmod(max(0, self.shop_time_left), 60)
        self.shop_timer_label.config(text=f"🔄 Restocks in {minutes:02d}:{seconds:02d}")

    # ------------------------------------------------------------------
    # BIOMES
    # ------------------------------------------------------------------
    def _biome_tick(self):
        self.biome_time_left -= 1
        if self.biome_time_left <= 0:
            self._roll_next_biome()
        else:
            self._update_biome_banner()
        self.root.after(1000, self._biome_tick)

    def _roll_next_biome(self):
        weights = [b["weight"] for b in BIOMES]
        self.current_biome = random.choices(BIOMES, weights=weights, k=1)[0]
        self.biome_time_left = BIOME_ROTATE_SECONDS
        self._update_biome_banner()

    def _update_biome_banner(self):
        if not hasattr(self, "biome_label_update"):
            return
        biome = self.current_biome
        minutes, seconds = divmod(max(0, self.biome_time_left), 60)
        if biome["scope"]:
            text = f"🌎 {biome['name']}  ·  +{biome['boost_pct']}% {biome['scope']} odds  ·  changes in {minutes:02d}:{seconds:02d}"
        else:
            text = f"🌎 {biome['name']}  ·  no active effect  ·  changes in {minutes:02d}:{seconds:02d}"
        self.biome_label_update(text, biome["color"])

    # ------------------------------------------------------------------
    # ACHIEVEMENTS
    # ------------------------------------------------------------------
    def _check_achievements(self):
        newly_completed = []
        for ach in ACHIEVEMENTS:
            if ach["name"] in self.completed_achievements:
                continue
            if ach["check"](self):
                self.completed_achievements.add(ach["name"])
                self.currency += ach["reward"]
                newly_completed.append(ach)

        if newly_completed:
            self._update_status_bar()
            if hasattr(self, "index_tab"):
                self.refresh_index_tab()
            for ach in newly_completed:
                messagebox.showinfo(
                    "🏅 Achievement Unlocked!",
                    f"{ach['name']}\n{ach['desc']}\n+{ach['reward']} coins",
                )

    # ------------------------------------------------------------------
    # CRAFT TAB
    # ------------------------------------------------------------------
    def refresh_craft_tab(self):
        self._rebuild_scrollable(self.craft_tab, self._populate_craft, top_bar_fn=self._build_craft_top_bar)

    def _build_craft_top_bar(self, parent):
        header = tk.Frame(parent, bg=PALETTE["base"], padx=16, pady=12)
        header.pack(fill="x")

        tk.Label(
            header, text="Crafting", font=FONT_HEADER,
            bg=PALETTE["base"], fg=PALETTE["text"],
        ).pack(side="left")

        toggle = tk.Checkbutton(
            header, text="Auto-Craft", variable=self.auto_craft_var,
            font=FONT_SMALL, bg=PALETTE["base"], fg=PALETTE["text"],
            activebackground=PALETTE["base"], activeforeground=PALETTE["text"],
            selectcolor=PALETTE["surface1"], bd=0, highlightthickness=0,
            cursor="hand2",
        )
        toggle.pack(side="right")

        tk.Label(
            parent,
            text="Matching rolls are absorbed straight into materials for your active "
                 "recipe and can no longer be sold.",
            font=FONT_SMALL, bg=PALETTE["base"], fg=PALETTE["subtext"], wraplength=560, justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 6))

        status, status_inner = make_rounded_card(parent, PALETTE["surface0"], stretch_x=True)
        status.pack(fill="x", padx=16, pady=(0, 10))
        status_pad = tk.Frame(status_inner, bg=PALETTE["surface0"], padx=12, pady=10)
        status_pad.pack(fill="x")

        if self.active_recipe:
            recipe = self.active_recipe
            complete = self._recipe_complete(recipe)
            tk.Label(
                status_pad, text=f"Working on: {recipe['name']}", font=("Segoe UI", 11, "bold"),
                bg=PALETTE["surface0"], fg=PALETTE["accent"], anchor="w",
            ).pack(side="left")

            btn_color = PALETTE["green"] if complete else PALETTE["surface2"]
            craft_btn = SmoothButton(
                status_pad, "Craft Now" if complete else "Craft Now (locked)",
                command=self.craft_now if complete else None,
                bg=btn_color, hover_bg=blend_color(btn_color, PALETTE["white"], 0.2 if complete else 0),
                fg=PALETTE["mantle"] if complete else PALETTE["subtext"],
                font=FONT_SMALL, padx=14, pady=6, radius=9, shadow=False,
            )
            if not complete:
                craft_btn.config(state="disabled")
            craft_btn.pack(side="right")
        else:
            tk.Label(
                status_pad, text="No active recipe — pick one below to start gathering materials.",
                font=FONT_SMALL, bg=PALETTE["surface0"], fg=PALETTE["subtext"], anchor="w",
            ).pack(side="left")

    def _populate_craft(self, scroll_frame):
        # Equipped gear (permanent, already crafted)
        if self.crafted_gear:
            tk.Label(
                scroll_frame, text="EQUIPPED GEAR", font=("Segoe UI", 9, "bold"),
                bg=PALETTE["base"], fg=PALETTE["subtext"],
            ).pack(anchor="w", padx=16, pady=(10, 4))
            for recipe in self.crafted_gear:
                self._make_gear_card(scroll_frame, recipe)

        # Material storage
        if self.craft_materials and any(v > 0 for v in self.craft_materials.values()):
            tk.Label(
                scroll_frame, text="MATERIALS", font=("Segoe UI", 9, "bold"),
                bg=PALETTE["base"], fg=PALETTE["subtext"],
            ).pack(anchor="w", padx=16, pady=(14, 4))
            mat_row = tk.Frame(scroll_frame, bg=PALETTE["base"])
            mat_row.pack(fill="x", padx=16)
            for rarity in RARITIES:
                count = self.craft_materials.get(rarity, 0)
                if count <= 0:
                    continue
                chip = make_badge(mat_row, f"{rarity} ×{count}", RARITIES[rarity]["color"], PALETTE["base"])
                chip.pack(side="left", padx=(0, 6), pady=(0, 6))

        # Recipes not yet crafted
        tk.Label(
            scroll_frame, text="RECIPES", font=("Segoe UI", 9, "bold"),
            bg=PALETTE["base"], fg=PALETTE["subtext"],
        ).pack(anchor="w", padx=16, pady=(14, 4))

        crafted_names = {g["name"] for g in self.crafted_gear}
        remaining = [r for r in CRAFTING_RECIPES if r["name"] not in crafted_names]
        if not remaining:
            tk.Label(
                scroll_frame, text="You've crafted every recipe. Impressive!",
                font=FONT_BODY, bg=PALETTE["base"], fg=PALETTE["subtext"], pady=10,
            ).pack(anchor="w", padx=16)
        for recipe in remaining:
            self._make_recipe_card(scroll_frame, recipe)

    def _recipe_complete(self, recipe):
        return all(self.craft_materials.get(r, 0) >= n for r, n in recipe["materials"].items())

    def _describe_effect(self, effect):
        if effect["kind"] == "luck":
            return f"+{effect['boost_pct']}% odds for {effect['scope']} rarities, permanently."
        return f"+{effect['pct']}% coins from every sale, permanently."

    def _make_gear_card(self, parent, recipe):
        color = RARITIES[list(recipe["materials"].keys())[-1]]["color"]
        card, body = make_rounded_card(parent, PALETTE["surface0"], stretch_x=True)
        card.pack(fill="x", padx=16, pady=4)

        row = tk.Frame(body, bg=PALETTE["surface0"])
        row.pack(fill="both", expand=True)

        stripe_canvas = tk.Canvas(row, width=4, bg=PALETTE["surface0"], highlightthickness=0, bd=0)
        stripe_canvas.pack(side="left", fill="y")
        stripe_canvas.bind(
            "<Configure>",
            lambda e, c=stripe_canvas, col=color: (
                c.delete("all"),
                c.create_rectangle(0, 4, 4, e.height - 4, fill=col, outline=""),
            ),
        )

        inner = tk.Frame(row, bg=PALETTE["surface0"], padx=14, pady=10)
        inner.pack(side="left", fill="both", expand=True)

        tk.Label(
            inner, text=f"{recipe['name']}  ·  {recipe['type']}", font=("Segoe UI", 11, "bold"),
            bg=PALETTE["surface0"], fg=PALETTE["text"], anchor="w",
        ).pack(anchor="w")

        tk.Label(
            inner, text=self._describe_effect(recipe["effect"]), font=FONT_SMALL,
            bg=PALETTE["surface0"], fg=color, anchor="w",
        ).pack(anchor="w", pady=(2, 0))

    def _recipe_progress(self, recipe):
        total_needed = sum(recipe["materials"].values())
        total_have = sum(min(self.craft_materials.get(r, 0), n) for r, n in recipe["materials"].items())
        return total_have / total_needed if total_needed else 0.0

    def _make_recipe_card(self, parent, recipe):
        color = RARITIES[list(recipe["materials"].keys())[-1]]["color"]
        is_active = self.active_recipe is not None and self.active_recipe["name"] == recipe["name"]

        card, body = make_rounded_card(parent, PALETTE["surface0"], stretch_x=True)
        card.pack(fill="x", padx=16, pady=5)

        row = tk.Frame(body, bg=PALETTE["surface0"])
        row.pack(fill="both", expand=True)

        stripe_canvas = tk.Canvas(row, width=4, bg=PALETTE["surface0"], highlightthickness=0, bd=0)
        stripe_canvas.pack(side="left", fill="y")
        stripe_canvas.bind(
            "<Configure>",
            lambda e, c=stripe_canvas, col=color: (
                c.delete("all"),
                c.create_rectangle(0, 4, 4, e.height - 4, fill=col, outline=""),
            ),
        )

        inner = tk.Frame(row, bg=PALETTE["surface0"], padx=14, pady=10)
        inner.pack(side="left", fill="both", expand=True)

        top_row = tk.Frame(inner, bg=PALETTE["surface0"])
        top_row.pack(fill="x")
        tk.Label(
            top_row, text=f"{recipe['name']}  ·  {recipe['type']}", font=("Segoe UI", 11, "bold"),
            bg=PALETTE["surface0"], fg=PALETTE["text"], anchor="w",
        ).pack(side="left")

        tk.Label(
            inner, text=recipe["desc"], font=FONT_SMALL,
            bg=PALETTE["surface0"], fg=PALETTE["subtext"], anchor="w",
        ).pack(anchor="w", pady=(2, 6))

        bar = make_progress_bar(inner, 220, 8, self._recipe_progress(recipe), color)
        bar.pack(anchor="w", pady=(0, 4))

        progress_parts = []
        for rarity, need in recipe["materials"].items():
            have = min(self.craft_materials.get(rarity, 0), need)
            progress_parts.append(f"{rarity} {have}/{need}")
        tk.Label(
            inner, text="   ·   ".join(progress_parts), font=FONT_SMALL,
            bg=PALETTE["surface0"], fg=color, anchor="w",
        ).pack(anchor="w")

        tk.Label(
            inner, text=self._describe_effect(recipe["effect"]), font=FONT_SMALL,
            bg=PALETTE["surface0"], fg=PALETTE["subtext"], anchor="w",
        ).pack(anchor="w", pady=(2, 8))

        btn_row = tk.Frame(inner, bg=PALETTE["surface0"])
        btn_row.pack(anchor="e")

        if is_active:
            complete = self._recipe_complete(recipe)
            btn_color = PALETTE["green"] if complete else PALETTE["surface2"]
            btn = SmoothButton(
                btn_row, "Craft Now" if complete else "In Progress…",
                command=self.craft_now if complete else None,
                bg=btn_color, hover_bg=blend_color(btn_color, PALETTE["white"], 0.2 if complete else 0),
                fg=PALETTE["mantle"] if complete else PALETTE["subtext"],
                font=FONT_SMALL, padx=14, pady=6, radius=9, shadow=False,
            )
            if not complete:
                btn.config(state="disabled")
            btn.pack()
        else:
            btn = SmoothButton(
                btn_row, "Work on this", command=lambda r=recipe: self.set_active_recipe(r),
                bg=color, hover_bg=blend_color(color, PALETTE["white"], 0.2), fg=PALETTE["mantle"],
                font=FONT_SMALL, padx=14, pady=6, radius=9, shadow=False,
            )
            btn.pack()

    def set_active_recipe(self, recipe):
        self.active_recipe = recipe
        self.refresh_craft_tab()

    def craft_now(self):
        recipe = self.active_recipe
        if not recipe or not self._recipe_complete(recipe):
            return

        for rarity, need in recipe["materials"].items():
            self.craft_materials[rarity] -= need

        self.crafted_gear.append(recipe)
        effect = recipe["effect"]
        if effect["kind"] == "luck":
            self.permanent_boosts.append({
                "name": recipe["name"],
                "kind": "luck",
                "scope": effect["scope"],
                "affected": SCOPE_RARITIES[effect["scope"]],
                "multiplier": 1 + effect["boost_pct"] / 100,
                "boost_pct": effect["boost_pct"],
            })
        else:
            self.permanent_boosts.append({
                "name": recipe["name"],
                "kind": "sell_bonus",
                "pct": effect["pct"],
            })

        self.active_recipe = None
        self._update_status_bar()
        self._refresh_boosts_strip()
        self.refresh_craft_tab()
        messagebox.showinfo("Crafted!", f"{recipe['name']} complete!\n{self._describe_effect(effect)}")

    # ------------------------------------------------------------------
    # INDEX TAB (achievements + lifetime collection log)
    # ------------------------------------------------------------------
    def refresh_index_tab(self):
        self._rebuild_scrollable(self.index_tab, self._populate_index, top_bar_fn=self._build_index_top_bar)

    def _build_index_top_bar(self, parent):
        header = tk.Frame(parent, bg=PALETTE["base"], padx=16, pady=12)
        header.pack(fill="x")
        tk.Label(
            header, text="Index", font=FONT_HEADER,
            bg=PALETTE["base"], fg=PALETTE["text"],
        ).pack(side="left")

        total_unique = sum(len(items) for items in ITEM_POOL.values())
        discovered = len(self.first_discovered)
        pct = int(round(100 * discovered / total_unique)) if total_unique else 0
        tk.Label(
            header, text=f"{discovered}/{total_unique} discovered ({pct}%)",
            font=FONT_BODY, bg=PALETTE["base"], fg=PALETTE["subtext"],
        ).pack(side="right")

    def _populate_index(self, scroll_frame):
        # Achievements
        tk.Label(
            scroll_frame, text="ACHIEVEMENTS", font=("Segoe UI", 9, "bold"),
            bg=PALETTE["base"], fg=PALETTE["subtext"],
        ).pack(anchor="w", padx=16, pady=(10, 4))

        done = sum(1 for a in ACHIEVEMENTS if a["name"] in self.completed_achievements)
        bar = make_progress_bar(scroll_frame, 220, 8, done / len(ACHIEVEMENTS) if ACHIEVEMENTS else 0, PALETTE["accent"])
        bar.pack(anchor="w", padx=16, pady=(0, 6))

        for ach in ACHIEVEMENTS:
            self._make_achievement_card(scroll_frame, ach)

        # Lifetime collection log
        tk.Label(
            scroll_frame, text="COLLECTION LOG", font=("Segoe UI", 9, "bold"),
            bg=PALETTE["base"], fg=PALETTE["subtext"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        for rarity in RARITIES:
            color = RARITIES[rarity]["color"]
            items = ITEM_POOL[rarity]
            found_in_tier = sum(1 for i in items if i in self.first_discovered)

            section = tk.Frame(scroll_frame, bg=PALETTE["base"])
            section.pack(fill="x", padx=16, pady=(10, 4))
            badge = make_badge(section, f"{rarity}  ({found_in_tier}/{len(items)})", color, PALETTE["base"])
            badge.pack(anchor="w")

            for item_name in items:
                self._make_index_entry_card(scroll_frame, item_name, color)

    def _make_achievement_card(self, parent, ach):
        unlocked = ach["name"] in self.completed_achievements
        color = PALETTE["green"] if unlocked else PALETTE["surface2"]

        card, body = make_rounded_card(parent, PALETTE["surface0"], stretch_x=True)
        card.pack(fill="x", padx=16, pady=3)

        row = tk.Frame(body, bg=PALETTE["surface0"])
        row.pack(fill="both", expand=True)

        stripe_canvas = tk.Canvas(row, width=4, bg=PALETTE["surface0"], highlightthickness=0, bd=0)
        stripe_canvas.pack(side="left", fill="y")
        stripe_canvas.bind(
            "<Configure>",
            lambda e, c=stripe_canvas, col=color: (
                c.delete("all"),
                c.create_rectangle(0, 4, 4, e.height - 4, fill=col, outline=""),
            ),
        )

        inner = tk.Frame(row, bg=PALETTE["surface0"], padx=12, pady=8)
        inner.pack(side="left", fill="both", expand=True)

        top = tk.Frame(inner, bg=PALETTE["surface0"])
        top.pack(fill="x")
        icon = "✅" if unlocked else "🔒"
        tk.Label(
            top, text=f"{icon} {ach['name']}", font=("Segoe UI", 10, "bold"),
            bg=PALETTE["surface0"], fg=PALETTE["text"] if unlocked else PALETTE["subtext"], anchor="w",
        ).pack(side="left")
        tk.Label(
            top, text=f"+{ach['reward']} coins", font=FONT_SMALL,
            bg=PALETTE["surface0"], fg=PALETTE["yellow"] if unlocked else PALETTE["subtext"],
        ).pack(side="right")

        tk.Label(
            inner, text=ach["desc"], font=FONT_SMALL,
            bg=PALETTE["surface0"], fg=PALETTE["subtext"], anchor="w",
        ).pack(anchor="w", pady=(2, 0))

    def _make_index_entry_card(self, parent, item_name, color):
        discovered = item_name in self.first_discovered
        card, body = make_rounded_card(parent, PALETTE["surface0"], stretch_x=True)
        card.pack(fill="x", padx=16, pady=3)

        row = tk.Frame(body, bg=PALETTE["surface0"])
        row.pack(fill="both", expand=True)

        stripe_canvas = tk.Canvas(row, width=4, bg=PALETTE["surface0"], highlightthickness=0, bd=0)
        stripe_canvas.pack(side="left", fill="y")
        stripe_color = color if discovered else PALETTE["surface2"]
        stripe_canvas.bind(
            "<Configure>",
            lambda e, c=stripe_canvas, col=stripe_color: (
                c.delete("all"),
                c.create_rectangle(0, 4, 4, e.height - 4, fill=col, outline=""),
            ),
        )

        content = tk.Frame(row, bg=PALETTE["surface0"], padx=12, pady=8)
        content.pack(side="left", fill="both", expand=True)

        if discovered:
            tk.Label(
                content, text=item_name, font=FONT_BODY,
                bg=PALETTE["surface0"], fg=PALETTE["text"], anchor="w",
            ).pack(side="left")
            tk.Label(
                content, text=f"found ×{self.lifetime_item_counts[item_name]}  ·  1st on roll #{self.first_discovered[item_name]}",
                font=FONT_SMALL, bg=PALETTE["surface0"], fg=PALETTE["subtext"],
            ).pack(side="right")
        else:
            tk.Label(
                content, text="??? — not yet discovered", font=FONT_BODY,
                bg=PALETTE["surface0"], fg=PALETTE["subtext"], anchor="w",
            ).pack(side="left")

    # ------------------------------------------------------------------
    # MINESWEEPER MINIGAME
    # ------------------------------------------------------------------
    def refresh_mine_tab(self):
        self._rebuild_scrollable(self.mine_tab, self._populate_mine, top_bar_fn=self._build_mine_top_bar)

    def _mine_status_text(self):
        g = self.mine_game
        if not g:
            return "No game in progress"
        if g["over"]:
            return "💥 You lost — pick a difficulty to try again" if g["lost"] else "💎 You won! Pick a difficulty to play again"
        remaining_safe = g["rows"] * g["cols"] - g["mines"] - g["revealed_count"]
        return f"{g['difficulty_name']}  ·  {remaining_safe} safe cells left  ·  {g['mines']} 💣"

    def _build_mine_top_bar(self, parent):
        header = tk.Frame(parent, bg=PALETTE["base"], padx=16, pady=12)
        header.pack(fill="x")

        tk.Label(
            header, text="Minesweeper", font=FONT_HEADER,
            bg=PALETTE["base"], fg=PALETTE["text"],
        ).pack(side="left")

        self.mine_status_label = tk.Label(
            header, text=self._mine_status_text(), font=FONT_BODY,
            bg=PALETTE["base"], fg=PALETTE["subtext"],
        )
        self.mine_status_label.pack(side="right")

        tk.Label(
            parent, text="Left-click to reveal a cell, right-click to flag a suspected mine. "
                         "Clear every safe cell to win coins — hit a mine and you lose your entry fee.",
            font=FONT_SMALL, bg=PALETTE["base"], fg=PALETTE["subtext"], wraplength=560, justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 10))

        diff_row = tk.Frame(parent, bg=PALETTE["base"])
        diff_row.pack(anchor="w", padx=16, pady=(0, 12))
        for diff in MINE_DIFFICULTIES:
            btn = SmoothButton(
                diff_row, f"{diff['name']}  ·  {diff['cost']}c to play  ·  win {diff['reward']}c",
                command=lambda d=diff: self.start_mine_game(d),
                bg=PALETTE["surface2"], hover_bg=PALETTE["surface1"], fg=PALETTE["text"],
                font=FONT_SMALL, padx=12, pady=7, radius=9, shadow=False,
            )
            btn.pack(side="left", padx=(0, 8))

    def _populate_mine(self, scroll_frame):
        if not self.mine_game:
            tk.Label(
                scroll_frame, text="Pick a difficulty above to start a new game.",
                font=FONT_BODY, bg=PALETTE["base"], fg=PALETTE["subtext"], pady=20,
            ).pack()
            return
        self._build_mine_board(scroll_frame)

    def _build_mine_board(self, parent):
        g = self.mine_game
        board_card, board_body = make_rounded_card(parent, PALETTE["surface0"])
        board_card.pack(padx=16, pady=(0, 16))
        board_pad = tk.Frame(board_body, bg=PALETTE["surface0"], padx=10, pady=10)
        board_pad.pack()

        g["buttons"] = [[None] * g["cols"] for _ in range(g["rows"])]
        cell_size = 24 if g["rows"] <= 10 else 20
        for r in range(g["rows"]):
            for c in range(g["cols"]):
                btn = tk.Button(
                    board_pad, text="", width=2, height=1, font=("Consolas", 9, "bold"),
                    bg=PALETTE["surface2"], fg=PALETTE["text"], relief="flat", bd=0,
                    activebackground=PALETTE["surface1"], highlightthickness=0,
                )
                btn.grid(row=r, column=c, padx=1, pady=1, ipadx=0, ipady=0)
                btn.bind("<Button-1>", lambda e, rr=r, cc=c: self.reveal_cell(rr, cc))
                btn.bind("<Button-3>", lambda e, rr=r, cc=c: self.flag_cell(rr, cc))
                g["buttons"][r][c] = btn

                text, bg, fg = self._mine_cell_visual(g["grid"][r][c])
                btn.config(text=text, bg=bg, fg=fg)
                if g["over"]:
                    btn.unbind("<Button-1>")
                    btn.unbind("<Button-3>")

    def start_mine_game(self, difficulty):
        if self.currency < difficulty["cost"]:
            messagebox.showwarning("Not enough coins", "You can't afford to play this difficulty yet!")
            return

        self.currency -= difficulty["cost"]
        self._update_status_bar()

        rows, cols, mines = difficulty["rows"], difficulty["cols"], difficulty["mines"]
        grid = [
            [{"is_mine": False, "revealed": False, "flagged": False, "adjacent": 0} for _ in range(cols)]
            for _ in range(rows)
        ]
        self.mine_game = {
            "rows": rows, "cols": cols, "mines": mines,
            "cost": difficulty["cost"], "reward": difficulty["reward"], "difficulty_name": difficulty["name"],
            "grid": grid, "mines_placed": False, "over": False, "lost": False,
            "revealed_count": 0, "buttons": [],
        }
        self.refresh_mine_tab()

    def _place_mines(self, safe_r, safe_c):
        """Mines are placed only after the first click, and never in the
        clicked cell or its immediate neighbors, so the first reveal is
        always safe — standard Minesweeper fairness rule."""
        g = self.mine_game
        all_cells = [(r, c) for r in range(g["rows"]) for c in range(g["cols"])]
        safe_zone = {(safe_r + dr, safe_c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        candidates = [cell for cell in all_cells if cell not in safe_zone]
        mine_count = min(g["mines"], len(candidates))
        for (r, c) in random.sample(candidates, mine_count):
            g["grid"][r][c]["is_mine"] = True

        for r in range(g["rows"]):
            for c in range(g["cols"]):
                if g["grid"][r][c]["is_mine"]:
                    continue
                count = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < g["rows"] and 0 <= nc < g["cols"] and g["grid"][nr][nc]["is_mine"]:
                            count += 1
                g["grid"][r][c]["adjacent"] = count
        g["mines_placed"] = True

    def reveal_cell(self, r, c):
        g = self.mine_game
        if not g or g["over"]:
            return
        cell = g["grid"][r][c]
        if cell["revealed"] or cell["flagged"]:
            return

        if not g["mines_placed"]:
            self._place_mines(r, c)

        if cell["is_mine"]:
            self._mine_game_over(won=False)
            return

        # Flood-fill reveal (iterative, to avoid recursion limits on big boards)
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            ccell = g["grid"][cr][cc]
            if ccell["revealed"] or ccell["flagged"]:
                continue
            ccell["revealed"] = True
            g["revealed_count"] += 1
            self._update_mine_cell_appearance(cr, cc)
            if ccell["adjacent"] == 0:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < g["rows"] and 0 <= nc < g["cols"]:
                            ncell = g["grid"][nr][nc]
                            if not ncell["revealed"] and not ncell["flagged"] and not ncell["is_mine"]:
                                stack.append((nr, nc))

        total_safe = g["rows"] * g["cols"] - g["mines"]
        if g["revealed_count"] >= total_safe:
            self._mine_game_over(won=True)
        else:
            self._update_mine_status()

    def flag_cell(self, r, c):
        g = self.mine_game
        if not g or g["over"]:
            return
        cell = g["grid"][r][c]
        if cell["revealed"]:
            return
        cell["flagged"] = not cell["flagged"]
        self._update_mine_cell_appearance(r, c)

    def _mine_cell_visual(self, cell):
        if cell["flagged"]:
            return "🚩", PALETTE["surface2"], PALETTE["red"]
        if not cell["revealed"]:
            return "", PALETTE["surface2"], PALETTE["text"]
        if cell["is_mine"]:
            return "💣", PALETTE["red"], PALETTE["mantle"]
        if cell["adjacent"] == 0:
            return "", PALETTE["surface0"], PALETTE["text"]
        return str(cell["adjacent"]), PALETTE["surface0"], MINE_NUMBER_COLORS.get(cell["adjacent"], PALETTE["text"])

    def _update_mine_cell_appearance(self, r, c):
        g = self.mine_game
        text, bg, fg = self._mine_cell_visual(g["grid"][r][c])
        g["buttons"][r][c].config(text=text, bg=bg, fg=fg)

    def _mine_game_over(self, won):
        g = self.mine_game
        g["over"] = True
        g["lost"] = not won

        for r in range(g["rows"]):
            for c in range(g["cols"]):
                cell = g["grid"][r][c]
                if cell["is_mine"]:
                    cell["revealed"] = True
                    self._update_mine_cell_appearance(r, c)
                g["buttons"][r][c].unbind("<Button-1>")
                g["buttons"][r][c].unbind("<Button-3>")

        self._update_mine_status()
        if won:
            self.currency += g["reward"]
            self._update_status_bar()
            self._check_achievements()
            messagebox.showinfo("💎 You win!", f"Cleared the board! +{g['reward']} coins")
        else:
            messagebox.showinfo("💥 Boom!", "You hit a mine. Better luck next time!")

    def _update_mine_status(self):
        if hasattr(self, "mine_status_label"):
            self.mine_status_label.config(text=self._mine_status_text())

    # ------------------------------------------------------------------
    # ODDS TAB
    # ------------------------------------------------------------------
    def _build_odds_tab(self):
        frame = self.odds_tab
        tk.Label(
            frame, text="Drop Rates", font=FONT_HEADER,
            bg=PALETTE["base"], fg=PALETTE["text"],
        ).pack(pady=(22, 14))

        total_weight = sum(r["weight"] for r in RARITIES.values())
        for rarity, info in RARITIES.items():
            pct = info["weight"] / total_weight * 100

            row = tk.Frame(frame, bg=PALETTE["surface0"])
            row.pack(fill="x", padx=30, pady=4)

            stripe = tk.Frame(row, bg=info["color"], width=4)
            stripe.pack(side="left", fill="y")

            inner = tk.Frame(row, bg=PALETTE["surface0"])
            inner.pack(side="left", fill="both", expand=True, padx=14, pady=10)

            tk.Label(
                inner, text=rarity, font=("Segoe UI", 11, "bold"),
                bg=PALETTE["surface0"], fg=info["color"], width=13, anchor="w",
            ).pack(side="left")

            tk.Label(
                inner, text=f"{pct:5.2f}%", font=FONT_BODY,
                bg=PALETTE["surface0"], fg=PALETTE["text"], width=8, anchor="w",
            ).pack(side="left")

            tk.Label(
                inner, text=f"sells for {info['sell_value']} coin(s)", font=FONT_SMALL,
                bg=PALETTE["surface0"], fg=PALETTE["subtext"],
            ).pack(side="left")

    # ------------------------------------------------------------------
    # SHARED HELPERS
    # ------------------------------------------------------------------
    def _rebuild_scrollable(self, tab, populate_fn, top_bar_fn=None):
        for widget in tab.winfo_children():
            widget.destroy()

        if top_bar_fn:
            top_bar_fn(tab)

        container = tk.Frame(tab, bg=PALETTE["base"])
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=PALETTE["base"], borderwidth=0, highlightthickness=0)
        scroll_frame = tk.Frame(canvas, bg=PALETTE["base"])
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        self._bind_mousewheel(canvas)
        populate_fn(scroll_frame)

    def _bind_mousewheel(self, canvas):
        """Let the mouse wheel scroll whichever scrollable canvas the
        cursor is currently over (Windows/Mac use <MouseWheel>, Linux
        uses <Button-4>/<Button-5>)."""
        def _on_wheel(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind(_event):
            canvas.bind_all("<MouseWheel>", _on_wheel)
            canvas.bind_all("<Button-4>", _on_wheel)
            canvas.bind_all("<Button-5>", _on_wheel)

        def _unbind(_event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind)
        canvas.bind("<Leave>", _unbind)

    def _update_status_bar(self):
        self._animate_currency(self.currency)
        self._rolls_pill_update(f"🎲 {self.total_rolls} rolls")

    def _animate_currency(self, target):
        """Smoothly count the coin pill up/down to its new value instead
        of snapping instantly, so big wins and purchases feel tangible."""
        current = getattr(self, "_currency_display", target)
        if current == target:
            self._currency_display = target
            self._coin_pill_update(f"💰 {target}")
            return

        if getattr(self, "_currency_anim_job", None):
            try:
                self.root.after_cancel(self._currency_anim_job)
            except Exception:
                pass

        steps = 10
        diff = target - current

        def step(i=0):
            value = target if i >= steps else int(round(current + diff * (i + 1) / steps))
            self._currency_display = value
            self._coin_pill_update(f"💰 {value}")
            if i < steps:
                self._currency_anim_job = self.root.after(20, lambda: step(i + 1))
            else:
                self._currency_anim_job = None

        step()


def main():
    root = tk.Tk()
    app = RNGGameApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()