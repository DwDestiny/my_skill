#!/usr/bin/env python3

# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by skills/visual-ppt-deck-builder/scripts/render_style_background.py
# Pos: skills/visual-ppt-deck-builder/scripts/render_style_background.py
"""Test-only placeholder background renderer.

正式风格候选不得使用本脚本输出作为商业设计素材。本脚本只服务
build_style_candidates.js --allow-placeholder-backgrounds 的结构测试，
真实样张必须使用 Codex imagegen、Skywork Design、用户模板反拆或
用户提供的 raster 背景。
"""

import argparse
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


canvas_width = 1920
canvas_height = 1080
slide_width = 13.333
slide_height = 7.5


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--style-slug", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--blueprint-json", required=True)
    return parser.parse_args()


def to_pixels(zone):
    return {
        "x0": int(zone["x"] / slide_width * canvas_width),
        "y0": int(zone["y"] / slide_height * canvas_height),
        "x1": int((zone["x"] + zone["w"]) / slide_width * canvas_width),
        "y1": int((zone["y"] + zone["h"]) / slide_height * canvas_height),
    }


def rgba(hex_color, alpha=255):
    raw = hex_color.replace("#", "")
    return tuple(int(raw[index:index + 2], 16) for index in (0, 2, 4)) + (alpha,)


def new_layer():
    return Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))


def apply_vertical_gradient(base, top_hex, bottom_hex):
    top = rgba(top_hex)
    bottom = rgba(bottom_hex)
    pixels = []
    for y_index in range(canvas_height):
        ratio = y_index / max(1, canvas_height - 1)
        pixels.extend(
            [
                (
                    int(top[0] + (bottom[0] - top[0]) * ratio),
                    int(top[1] + (bottom[1] - top[1]) * ratio),
                    int(top[2] + (bottom[2] - top[2]) * ratio),
                    255,
                )
            ]
            * canvas_width
        )
    gradient = Image.new("RGBA", (canvas_width, canvas_height))
    gradient.putdata(pixels)
    return Image.alpha_composite(base, gradient)


def add_grain(base, amount=12, seed=7):
    rng = random.Random(seed)
    noise = Image.new("L", (canvas_width, canvas_height))
    noise.putdata([rng.randint(120 - amount, 136 + amount) for _ in range(canvas_width * canvas_height)])
    rgb_noise = Image.merge("RGBA", (noise, noise, noise, Image.new("L", (canvas_width, canvas_height), 24)))
    return Image.alpha_composite(base, rgb_noise)


def draw_soft_blob(layer, bbox, color_hex, alpha=120, blur=38):
    blob = new_layer()
    draw = ImageDraw.Draw(blob)
    draw.ellipse(bbox, fill=rgba(color_hex, alpha))
    blob = blob.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(blob)


def draw_soft_rect(layer, bbox, color_hex, alpha=80, blur=24):
    rect = new_layer()
    draw = ImageDraw.Draw(rect)
    draw.rounded_rectangle(bbox, radius=32, fill=rgba(color_hex, alpha))
    rect = rect.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(rect)


def draw_line_cluster(layer, points, color_hex, alpha=90, width=3, blur=0):
    scratch = new_layer()
    draw = ImageDraw.Draw(scratch)
    draw.line(points, fill=rgba(color_hex, alpha), width=width)
    if blur:
      scratch = scratch.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(scratch)


def draw_polyline(layer, points, color_hex, alpha=100, width=3, blur=0):
    scratch = new_layer()
    draw = ImageDraw.Draw(scratch)
    draw.line(points, fill=rgba(color_hex, alpha), width=width, joint="curve")
    if blur:
        scratch = scratch.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(scratch)


def draw_polygon(layer, points, color_hex, alpha=120, blur=0):
    scratch = new_layer()
    draw = ImageDraw.Draw(scratch)
    draw.polygon(points, fill=rgba(color_hex, alpha))
    if blur:
        scratch = scratch.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(scratch)


def draw_grid(layer, origin_x, origin_y, width, height, color_hex, alpha=35, step=64, line_width=1):
    scratch = new_layer()
    draw = ImageDraw.Draw(scratch)
    for x_index in range(origin_x, origin_x + width + 1, step):
        draw.line((x_index, origin_y, x_index, origin_y + height), fill=rgba(color_hex, alpha), width=line_width)
    for y_index in range(origin_y, origin_y + height + 1, step):
        draw.line((origin_x, y_index, origin_x + width, y_index), fill=rgba(color_hex, alpha), width=line_width)
    layer.alpha_composite(scratch)


def draw_architecture_anchor(layer):
    draw_polygon(layer, [(1180, 0), (1920, 0), (1920, 1080), (1400, 1080), (1110, 350)], "D3D9E0", alpha=178)
    draw_polygon(layer, [(1400, 0), (1920, 0), (1920, 1080), (1600, 1080), (1330, 220)], "EEF1F4", alpha=170)
    for offset in range(0, 9):
        x_top = 1240 + offset * 78
        draw_line_cluster(layer, [(x_top, 0), (x_top + 230, 1080)], "687481", alpha=118, width=3)
    for y_line in range(140, 1040, 140):
        draw_line_cluster(layer, [(1120, y_line), (1900, y_line + 64)], "8E9AA6", alpha=92, width=3)
    draw_soft_blob(layer, (1260, 500, 1980, 1180), "B5C0CB", alpha=132, blur=76)


def draw_playful_classroom_anchor(layer):
    draw_soft_blob(layer, (-120, 560, 520, 1140), "8FD3FF", alpha=190, blur=74)
    draw_soft_blob(layer, (1260, -80, 1980, 360), "FFD76B", alpha=178, blur=86)
    draw_soft_blob(layer, (1420, 690, 2040, 1200), "FFB7CF", alpha=170, blur=86)
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle((78, 690, 500, 944), radius=50, fill=rgba("FFE4A3", 248), outline=rgba("F59E0B", 128), width=5)
    draw.ellipse((166, 464, 338, 636), fill=rgba("FFD5B8", 255))
    draw.pieslice((128, 418, 370, 620), 195, 350, fill=rgba("513A2B", 255))
    draw.rounded_rectangle((126, 620, 378, 826), radius=62, fill=rgba("FF8FB1", 255))
    draw.line((168, 684, 96, 784), fill=rgba("FFD5B8", 255), width=24)
    draw.line((334, 682, 438, 596), fill=rgba("FFD5B8", 255), width=22)
    for x_eye in [214, 282]:
        draw.ellipse((x_eye, 535, x_eye + 16, 551), fill=rgba("1F2937", 245))
    draw.arc((220, 558, 294, 606), 20, 160, fill=rgba("D65A70", 220), width=5)
    for star_x, star_y, color_hex in [(520, 260, "FFC93C"), (605, 210, "FF9EB5"), (690, 272, "8FD3FF"), (1510, 160, "7BDDC8")]:
        draw.regular_polygon((star_x, star_y, 22), n_sides=5, rotation=18, fill=rgba(color_hex, 210))


def draw_dashboard_anchor(layer):
    draw_grid(layer, 900, 105, 960, 810, "1D4F78", alpha=68, step=72)
    for index, value in enumerate([180, 290, 230, 380, 520, 460, 640]):
        x0 = 1040 + index * 92
        y0 = 780 - value
        draw_soft_rect(layer, (x0, y0, x0 + 54, 780), "12C7D6" if index % 2 else "5B5FF0", alpha=154, blur=10)
    points = [(980, 720), (1080, 650), (1180, 680), (1280, 560), (1380, 600), (1480, 470), (1600, 430), (1740, 330)]
    draw_polyline(layer, points, "12C7D6", alpha=182, width=6, blur=1)
    draw_polyline(layer, points, "5B5FF0", alpha=112, width=16, blur=14)
    draw_soft_blob(layer, (1220, 120, 1940, 840), "0B4F86", alpha=118, blur=130)


def draw_oriental_anchor(layer):
    draw_soft_blob(layer, (-120, 620, 580, 1160), "D9C6AA", alpha=98, blur=118)
    draw_soft_blob(layer, (1430, 620, 2040, 1160), "C72B2B", alpha=62, blur=138)
    draw_soft_blob(layer, (-80, 10, 420, 360), "B91C1C", alpha=50, blur=96)
    mountain_back = [(0, 880), (180, 700), (360, 770), (550, 590), (720, 760), (910, 630), (1080, 840)]
    mountain_front = [(0, 980), (210, 830), (430, 900), (610, 740), (820, 910), (1030, 790), (1260, 980)]
    draw_polyline(layer, mountain_back, "171717", alpha=72, width=12, blur=7)
    draw_polyline(layer, mountain_front, "171717", alpha=58, width=22, blur=14)
    draw = ImageDraw.Draw(layer)
    draw.ellipse((146, 88, 282, 224), fill=rgba("B91C1C", 218))
    draw.rectangle((1650, 130, 1735, 215), fill=rgba("B91C1C", 218))
    draw.line((1610, 116, 1760, 116), fill=rgba("B91C1C", 110), width=2)


def draw_tech_anchor(layer):
    draw_soft_blob(layer, (900, 580, 1880, 1280), "00D4D8", alpha=118, blur=150)
    draw_soft_blob(layer, (1080, 500, 1980, 1180), "7C4DFF", alpha=92, blur=160)
    draw = ImageDraw.Draw(layer)
    platform = [(1160, 790), (1460, 660), (1780, 780), (1480, 930)]
    draw.polygon(platform, fill=rgba("081D3B", 245), outline=rgba("00D4D8", 185))
    draw.rounded_rectangle((1360, 540, 1600, 720), radius=28, fill=rgba("09254F", 252), outline=rgba("00D4D8", 218), width=4)
    for line_x in range(1390, 1580, 36):
        draw.line((line_x, 722, line_x, 806), fill=rgba("00D4D8", 90), width=2)
    for radius, color_hex, alpha in [(270, "00D4D8", 84), (390, "2F80ED", 54), (520, "7C4DFF", 36)]:
        draw.ellipse((1480 - radius, 720 - radius, 1480 + radius, 720 + radius), outline=rgba(color_hex, min(220, alpha + 30)), width=5)
    draw_line_cluster(layer, [(1540, 140), (1740, 280)], "7C4DFF", alpha=86, width=2)
    draw_line_cluster(layer, [(1660, 900), (1840, 1020)], "00D4D8", alpha=72, width=2)


def draw_editorial_anchor(layer):
    draw_polygon(layer, [(1380, 0), (1920, 0), (1920, 1080), (1590, 1080), (1320, 420)], "D8C6B0", alpha=120, blur=0)
    draw_polygon(layer, [(1540, 90), (1910, 120), (1840, 780), (1480, 720)], "111827", alpha=48, blur=10)
    draw_soft_blob(layer, (1330, 40, 1980, 620), "C7B299", alpha=72, blur=120)
    draw_line_cluster(layer, [(108, 0), (108, 1080)], "1F2937", alpha=128, width=6)
    draw_line_cluster(layer, [(1480, 150), (1820, 150)], "D72638", alpha=66, width=3)
    draw = ImageDraw.Draw(layer)
    draw.rectangle((1635, 165, 1725, 255), fill=rgba("D72638", 180))
    draw.rectangle((1748, 784, 1840, 874), fill=rgba("FFFFFF", 155))


def draw_saas_anchor(layer):
    draw_soft_blob(layer, (1120, 120, 1980, 850), "BFE8FF", alpha=108, blur=110)
    draw_soft_blob(layer, (900, 660, 1900, 1200), "B8F1D4", alpha=96, blur=126)
    draw = ImageDraw.Draw(layer)
    panels = [
        (1250, 190, 1770, 360, "FFFFFF", 196),
        (1340, 410, 1880, 625, "FFFFFF", 180),
        (1190, 690, 1700, 900, "FFFFFF", 166),
    ]
    for x0, y0, x1, y1, color_hex, alpha in panels:
        draw.rounded_rectangle((x0, y0, x1, y1), radius=34, fill=rgba(color_hex, min(235, alpha + 24)), outline=rgba("93C5FD", 122), width=3)
        draw.line((x0 + 42, y0 + 54, x1 - 42, y0 + 54), fill=rgba("2563EB", 128), width=4)
        for dot_index in range(3):
            draw.ellipse((x0 + 44 + dot_index * 28, y0 + 22, x0 + 56 + dot_index * 28, y0 + 34), fill=rgba("22C55E" if dot_index == 1 else "2563EB", 130))
    draw_line_cluster(layer, [(0, 0), (0, 1080)], "2563EB", alpha=220, width=14)


def draw_investor_anchor(layer):
    draw_grid(layer, 980, 130, 880, 800, "1A2C43", alpha=58, step=86)
    draw_soft_blob(layer, (1200, 80, 2020, 980), "F6C85F", alpha=52, blur=145)
    growth_points = [(1040, 820), (1160, 760), (1280, 650), (1400, 680), (1540, 500), (1700, 390), (1840, 300)]
    draw_polyline(layer, growth_points, "F6C85F", alpha=210, width=6, blur=1)
    draw_polyline(layer, growth_points, "F6C85F", alpha=112, width=20, blur=18)
    draw = ImageDraw.Draw(layer)
    for index, (x_point, y_point) in enumerate(growth_points):
        draw.ellipse((x_point - 8, y_point - 8, x_point + 8, y_point + 8), fill=rgba("F6C85F", 230))
        if index in [2, 4, 6]:
            draw.line((x_point, y_point, x_point + 56, y_point - 52), fill=rgba("F6C85F", 86), width=2)


def soften_safe_zone(base, zone, fill_hex, alpha=82, blur=26):
    expand_x = max(120, blur * 5)
    expand_y = max(90, blur * 4)
    radius = max(120, blur * 3)
    mask = Image.new("L", (canvas_width, canvas_height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        (zone["x0"] - expand_x, zone["y0"] - expand_y, zone["x1"] + expand_x, zone["y1"] + expand_y),
        radius=radius,
        fill=alpha,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(max(54, blur * 2)))
    overlay = Image.new("RGBA", (canvas_width, canvas_height), rgba(fill_hex, 0))
    overlay.putalpha(mask)
    return Image.alpha_composite(base, overlay)


def minimal_premium(base, zones):
    base = apply_vertical_gradient(base, "FFFFFF", "F3F3F3")
    layer = new_layer()
    draw_architecture_anchor(layer)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "FFFFFF", alpha=94, blur=32)
    base = soften_safe_zone(base, zones["chart_zone"], "F8FAFB", alpha=88, blur=28)
    return add_grain(base, amount=5, seed=11)


def playful_anime(base, zones):
    base = apply_vertical_gradient(base, "FFF6E6", "FFF0D6")
    layer = new_layer()
    draw_playful_classroom_anchor(layer)
    draw_soft_blob(layer, (420, 80, 980, 420), "FFF9EF", alpha=84, blur=72)
    for dot_x, dot_y, dot_color in [(1560, 100, "FFC93C"), (1640, 180, "FF9EB5"), (1720, 120, "8FD3FF"), (1520, 760, "7BDDC8")]:
        blob = new_layer()
        draw = ImageDraw.Draw(blob)
        draw.ellipse((dot_x, dot_y, dot_x + 22, dot_y + 22), fill=rgba(dot_color, 210))
        layer.alpha_composite(blob)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "FFF9ED", alpha=158, blur=38)
    base = soften_safe_zone(base, zones["chart_zone"], "FFF6E8", alpha=138, blur=34)
    return add_grain(base, amount=2, seed=17)


def data_analytics(base, zones):
    base = apply_vertical_gradient(base, "031022", "020814")
    layer = new_layer()
    draw_dashboard_anchor(layer)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "031022", alpha=104, blur=34)
    base = soften_safe_zone(base, zones["chart_zone"], "03162A", alpha=118, blur=38)
    return add_grain(base, amount=5, seed=23)


def oriental_heritage(base, zones):
    base = apply_vertical_gradient(base, "FAF5ED", "F2EBDD")
    layer = new_layer()
    draw_oriental_anchor(layer)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "FAF5ED", alpha=136, blur=34)
    base = soften_safe_zone(base, zones["chart_zone"], "F7F2E8", alpha=112, blur=30)
    return add_grain(base, amount=8, seed=29)


def future_tech(base, zones):
    base = apply_vertical_gradient(base, "03112A", "07122F")
    layer = new_layer()
    draw_tech_anchor(layer)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "061730", alpha=108, blur=34)
    base = soften_safe_zone(base, zones["chart_zone"], "04142E", alpha=106, blur=34)
    return add_grain(base, amount=5, seed=31)


def editorial_magazine(base, zones):
    base = apply_vertical_gradient(base, "FFFEFB", "F5F0E8")
    layer = new_layer()
    draw_editorial_anchor(layer)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "FFFDF9", alpha=150, blur=38)
    base = soften_safe_zone(base, zones["chart_zone"], "FFF9F2", alpha=152, blur=38)
    return add_grain(base, amount=3, seed=37)


def saas_product(base, zones):
    base = apply_vertical_gradient(base, "F8FBFF", "EEF5FB")
    layer = new_layer()
    draw_saas_anchor(layer)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "FBFDFF", alpha=122, blur=30)
    base = soften_safe_zone(base, zones["chart_zone"], "F6FBFF", alpha=96, blur=28)
    return add_grain(base, amount=4, seed=41)


def investor_narrative(base, zones):
    base = apply_vertical_gradient(base, "07101D", "0A1323")
    layer = new_layer()
    draw_investor_anchor(layer)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "07111F", alpha=110, blur=34)
    base = soften_safe_zone(base, zones["chart_zone"], "081522", alpha=74, blur=30)
    return add_grain(base, amount=5, seed=47)


style_renderers = {
    "minimal-premium": minimal_premium,
    "playful-anime": playful_anime,
    "data-analytics": data_analytics,
    "oriental-heritage": oriental_heritage,
    "future-tech": future_tech,
    "editorial-magazine": editorial_magazine,
    "saas-product": saas_product,
    "investor-narrative": investor_narrative,
}


def main():
    args = parse_args()
    blueprint = json.loads(args.blueprint_json)
    zones = {name: to_pixels(zone) for name, zone in blueprint["zones"].items()}
    base = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 255))
    renderer = style_renderers[args.style_slug]
    image = renderer(base, zones).convert("RGB")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=96)


if __name__ == "__main__":
    main()
