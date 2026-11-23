import turtle
import math
import random
import time

# ============================================================
# DIGITAL ROSE: a rose built entirely from binary characters
# ============================================================

WIDTH, HEIGHT = 1000, 850
BACKGROUND = "black"

screen = turtle.Screen()
screen.setup(WIDTH, HEIGHT)
screen.bgcolor(BACKGROUND)
screen.title("0100010001 | DIGITAL ROSE")
screen.tracer(0)

pen = turtle.Turtle(visible=False)
pen.penup()
pen.speed(0)

random.seed(12)

# Binary glyph colors: deep red shadows through bright rose highlights.
PETAL_PALETTE = [
    "#5A0010", "#850018", "#B00024", "#D00032",
    "#F00045", "#FF174F", "#FF4968", "#FF7890"
]
LEAF_PALETTE = ["#064D2B", "#087A3D", "#0AA653", "#35C878"]
CENTER_PALETTE = ["#FFB000", "#FFD34E", "#FFF0A0"]

# Each glyph is a tiny 0 or 1. Turtle writes text, not pixel dots.
def binary_glyph(x, y, char, color, size=7):
    pen.goto(x, y)
    pen.color(color)
    pen.write(char, align="center", font=("Courier", size, "bold"))

def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def rotate_point(x, y, angle):
    c, s = math.cos(angle), math.sin(angle)
    return x * c - y * s, x * s + y * c

# Petal shape: a rounded, tapered teardrop, generated in local coordinates.
def petal_point(u, v, length, width):
    # u runs from base (0) to tip (1); v runs across the petal (-1 to 1).
    bulge = math.sin(math.pi * u) ** 0.72
    px = length * u
    py = width * bulge * v
    return px, py

def point_in_petal(px, py, length, width):
    # Test point against the petal's tapered silhouette.
    u = px / length
    if not 0 <= u <= 1:
        return False
    bulge = math.sin(math.pi * u) ** 0.72
    if bulge < 0.015:
        return abs(py) < 1.5
    return abs(py) <= width * bulge

# Prebuild deterministic binary positions for each petal.
# Positions are denser near the petal edges to give a layered, woven look.
def make_petal_digits(length, width, spacing=9):
    points = []
    y = -width
    row = 0
    while y <= width:
        x = 0
        while x <= length:
            # Small stagger between rows resembles woven binary strands.
            xx = x + (spacing * 0.45 if row % 2 else 0)
            if point_in_petal(xx, y, length, width):
                points.append((xx, y, random.choice("01")))
            x += spacing
        y += spacing
        row += 1
    return points

# Petal layers: outer petals are broad; inner petals are shorter and curled inward.
PETALS = []
layers = [
    # count, length, width, radial distance, base angle, curl
    (7, 205, 83, 35, 0, 0.00),
    (6, 158, 68, 22, 18, 0.10),
    (5, 112, 54, 12, 36, 0.20),
    (4, 76, 42, 5, 48, 0.34),
]
for layer_index, (count, length, width, base_r, offset, curl) in enumerate(layers):
    for i in range(count):
        angle = math.radians(offset + i * (360 / count) + random.uniform(-5, 5))
        digits = make_petal_digits(length, width, 8 if layer_index < 2 else 7)
        PETALS.append({
            "length": length,
            "width": width,
            "base_r": base_r,
            "angle": angle,
            "curl": curl,
            "layer": layer_index,
            "digits": digits,
            "phase": random.random()
        })

# Leaf binary glyphs along a curved leaf silhouette.
def make_leaf_digits(length=145, width=48, spacing=9):
    result = []
    y = -width
    row = 0
    while y <= width:
        x = 0
        while x <= length:
            xx = x + (spacing / 2 if row % 2 else 0)
            u = xx / length
            if 0 <= u <= 1:
                half = width * (math.sin(math.pi * u) ** 0.85)
                if abs(y) <= half:
                    result.append((xx, y, random.choice("01")))
            x += spacing
        y += spacing
        row += 1
    return result

LEAF_DIGITS = make_leaf_digits()

def draw_leaf(anchor, angle, scale, progress, color_shift=0):
    ax, ay = anchor
    local_angle = math.radians(angle)
    # Reveal the leaf from its base toward its pointed tip.
    reveal = smoothstep(progress)
    for x, y, char in LEAF_DIGITS:
        if x > 145 * reveal:
            continue
        # Curved leaf axis.
        yy = y + 0.12 * x * math.sin(math.pi * x / 145)
        rx, ry = rotate_point(x * scale, yy * scale, local_angle)
        color = LEAF_PALETTE[(int(x / 30) + color_shift) % len(LEAF_PALETTE)]
        binary_glyph(ax + rx, ay + ry, char, color, 7)

def draw_stem(progress):
    # Stem grows upward from the bottom toward the flower head.
    top_y = -330 + 315 * smoothstep(progress)
    steps = 44
    for i in range(steps + 1):
        y = -330 + i * (top_y + 330) / steps
        x = 4 * math.sin(i * 0.11)
        if y <= top_y:
            binary_glyph(x, y, "0101"[i % 4], LEAF_PALETTE[i % len(LEAF_PALETTE)], 8)

    # Central stem highlight.
    for i in range(0, steps, 3):
        y = -320 + i * (top_y + 320) / steps
        if y <= top_y:
            binary_glyph(9 + 4 * math.sin(i * 0.11), y, "0", "#1B8F4D", 6)

def draw_petal(petal, bloom, frame):
    # Each layer opens at a slightly different rate for a natural unfurling.
    layer = petal["layer"]
    layer_start = [0.02, 0.12, 0.23, 0.34][layer]
    layer_progress = smoothstep((bloom - layer_start) / (1 - layer_start))
    if layer_progress <= 0:
        return

    # Outer petals spread farther; inner petals curl and lift.
    spread = [1.0, 0.83, 0.65, 0.48][layer]
    breathing = 1.0 + 0.018 * math.sin(frame * 0.045 + petal["phase"])
    scale_x = layer_progress * spread * breathing
    scale_y = layer_progress * (0.92 + 0.08 * breathing)

    # Fan the petal outward as it opens.
    angle = petal["angle"] + petal["curl"] * (1 - layer_progress)
    base_x = math.cos(petal["angle"]) * petal["base_r"] * layer_progress
    base_y = math.sin(petal["angle"]) * petal["base_r"] * layer_progress

    reveal_count = int(len(petal["digits"]) * layer_progress)
    # Smooth progressive reveal: glyphs emerge from the petal base outward.
    for idx, (u, v, char) in enumerate(petal["digits"][:reveal_count]):
        # Draw in local coordinates, with a gentle cup shape.
        px = u * scale_x
        py = (v * scale_y) + 0.0009 * (u ** 2) * scale_y
        # Tip curls inward slightly on inner layers.
        if layer >= 2:
            py += (u * u) * 8 * (1 - layer_progress)
        rx, ry = rotate_point(px, py, angle)
        x = base_x + rx
        y = base_y + ry + 105

        # Color changes across each petal, giving a red velvet gradient.
        palette_index = min(len(PETAL_PALETTE) - 1,
                            int((u / max(petal["length"], 1)) * 4)
                            + layer)
        color = PETAL_PALETTE[palette_index]
        # Bright edge glints appear as the bloom completes.
        if abs(v) > petal["width"] * 0.72 and layer_progress > 0.75:
            color = PETAL_PALETTE[min(7, palette_index + 2)]
        binary_glyph(x, y, char, color, 7)

def draw_rose_center(bloom, frame):
    if bloom < 0.55:
        return
    amount = smoothstep((bloom - 0.55) / 0.45)
    # Tiny spiraling binary core.
    for i in range(95):
        theta = i * 0.29 + frame * 0.006
        radius = (2 + i * 0.29) * amount
        x = math.cos(theta) * radius
        y = 105 + math.sin(theta) * radius
        binary_glyph(x, y, "01"[i % 2],
                     CENTER_PALETTE[i % len(CENTER_PALETTE)], 7)

def draw_title(frame):
    pen.goto(0, 365)
    pen.color("#FF4968")
    pen.write("0100010001", align="center",
              font=("Courier", 25, "bold"))
    pen.goto(0, 337)
    pen.color("#9B1835")
    pen.write("DIGITAL ROSE // BINARY BLOOM",
              align="center", font=("Courier", 11, "normal"))

def draw_scene(frame, bloom):
    pen.clear()

    # Draw the stem first so it sits behind the rose.
    draw_stem(min(1, bloom + 0.15))

    # Leaves unfold as the stem grows.
    draw_leaf((-2, -170), 155, 0.95, max(0, bloom - 0.18), 0)
    draw_leaf((2, -245), 25, 0.88, max(0, bloom - 0.28), 1)

    # Rose petals: back layers first, then inner layers.
    for petal in sorted(PETALS, key=lambda p: p["layer"]):
        draw_petal(petal, bloom, frame)

    draw_rose_center(bloom, frame)
    draw_title(frame)

    # A few floating binary sparks around the rose.
    for i in range(34):
        theta = i * 2.399 + frame * 0.008
        radius = 245 + 16 * math.sin(frame * 0.025 + i)
        x = math.cos(theta) * radius
        y = 100 + math.sin(theta) * radius
        char = "01"[(i + frame // 12) % 2]
        binary_glyph(x, y, char, "#5C1727", 7)

    screen.update()

# Opening bloom: eased, smooth, and slower near the end.
TOTAL_FRAMES = 150
for frame in range(TOTAL_FRAMES):
    p = frame / (TOTAL_FRAMES - 1)
    bloom = smoothstep(p)
    draw_scene(frame, bloom)
    time.sleep(0.025)

# Gentle breathing loop after the rose has fully opened.
frame = TOTAL_FRAMES
while True:
    breathe = 1.0 + 0.012 * math.sin(frame * 0.035)
    draw_scene(frame, min(1.0, breathe))
    frame += 1
    time.sleep(0.035)

turtle.done()
