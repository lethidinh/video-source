#!/usr/bin/env python3
"""Dựng video dọc 9:16 "Thức uống cho U40 muốn có vòng 2 eo thon" từ ảnh Pexels.

Chạy:  python3 scripts/build_video.py
Kết quả: output/eo-thon-u40.mp4
"""
import os
import subprocess
import textwrap
import urllib.request

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "images")
TMP = os.path.join(ROOT, "build")
OUT_DIR = os.path.join(ROOT, "output")
OUT = os.path.join(OUT_DIR, "eo-thon-u40.mp4")

W, H, FPS = 1080, 1920, 30
XF = 0.5  # thời lượng chuyển cảnh (giây)
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

PINK = (232, 62, 140)
GOLD = (255, 196, 0)
RED = (200, 16, 46)
WHITE = (255, 255, 255)

# (Pexels photo id, thời lượng, tiêu đề, phụ đề, màu nhấn, kiểu)
SCENES = [
    (5714313, 4.0, "THỨC UỐNG CHO U40", "muốn có vòng 2 eo thon", PINK, "hook"),
    (6551070, 4.5, "Cơ địa chai lì?", "Dễ lên – khó xuống!", RED, "normal"),
    (6787202, 4.0, "Chị em U30 – U40", "Áp dụng ngay điều này để có vòng 2 như ý đón Tết nhé!", PINK, "normal"),
    (1537268, 5.0, "1. Ăn gián đoạn 16/8", "16 tiếng nhịn – 8 tiếng ăn", GOLD, "step"),
    (1417945, 5.0, "2. Trà Unimate", "Dùng thay cho bữa sáng", GOLD, "step"),
    (4853710, 5.0, "3. Có Định đồng hành", "Hướng dẫn sát sao mỗi ngày", GOLD, "step"),
    (5935232, 4.0, "Vòng 2 như ý", "Kịp đón Tết nhé!", RED, "tet"),
    (1153370, 6.0, "Comment \"EO THON\"", "hoặc nhắn trực tiếp cho Định nhé!", PINK, "cta"),
]


def font(path, size):
    return ImageFont.truetype(path, size)


def download(pid):
    os.makedirs(IMG_DIR, exist_ok=True)
    path = os.path.join(IMG_DIR, f"pexels-{pid}.jpg")
    if not os.path.exists(path):
        url = (f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg"
               f"?auto=compress&cs=tinysrgb&w=1300&h=2310&fit=crop")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r, open(path, "wb") as f:
            f.write(r.read())
    return path


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def overlay_png(i, title, sub, accent, kind):
    """Khung chữ trong suốt đặt lên ảnh."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Dải tối phía dưới để chữ dễ đọc
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(H // 2, H):
        a = int(200 * (y - H // 2) / (H // 2))
        gd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img, grad)
    d = ImageDraw.Draw(img)

    ft = font(FONT_B, 86 if kind != "hook" else 92)
    fs = font(FONT_B, 54)
    max_w = W - 140
    # Thu nhỏ chữ để tiêu đề nằm gọn trên một dòng nếu có thể
    while d.textlength(title, font=ft) > max_w and ft.size > 64:
        ft = font(FONT_B, ft.size - 2)
    t_lines = wrap(d, title, ft, max_w)
    s_lines = wrap(d, sub, fs, max_w)

    lh_t, lh_s = ft.size + 18, fs.size + 14
    block_h = len(t_lines) * lh_t + 30 + len(s_lines) * lh_s
    y0 = H - 380 - block_h if kind != "hook" else 300

    # Thẻ màu sau tiêu đề
    for k, line in enumerate(t_lines):
        tw = d.textlength(line, font=ft)
        x = (W - tw) / 2
        y = y0 + k * lh_t
        d.rounded_rectangle([x - 30, y - 10, x + tw + 30, y + ft.size + 18],
                            radius=24, fill=accent + (235,))
        color = (40, 20, 0) if accent == GOLD else WHITE
        d.text((x, y), line, font=ft, fill=color)

    y = y0 + len(t_lines) * lh_t + 30
    for line in s_lines:
        tw = d.textlength(line, font=fs)
        x = (W - tw) / 2
        d.text((x, y), line, font=fs, fill=WHITE,
               stroke_width=4, stroke_fill=(0, 0, 0))
        y += lh_s

    # Nhãn thương hiệu nhỏ trên cùng
    fb = font(FONT_B, 40)
    tag = "Định • Đồng hành vóc dáng"
    tw = d.textlength(tag, font=fb)
    d.rounded_rectangle([(W - tw) / 2 - 26, 110, (W + tw) / 2 + 26, 178],
                        radius=34, fill=(0, 0, 0, 140))
    d.text(((W - tw) / 2, 120), tag, font=fb, fill=WHITE)

    if kind == "tet":
        fx = font(FONT_B, 70)
        txt = "🌸 ĐÓN TẾT 🌸".replace("🌸", "✿")
        tw = d.textlength(txt, font=fx)
        d.rounded_rectangle([(W - tw) / 2 - 40, 330, (W + tw) / 2 + 40, 440],
                            radius=20, fill=RED + (230,), outline=GOLD, width=6)
        d.text(((W - tw) / 2, 345), txt, font=fx, fill=GOLD)

    if kind == "cta":
        fx = font(FONT_B, 58)
        txt = "👇 Comment ngay 👇".replace("👇", "▼")
        tw = d.textlength(txt, font=fx)
        d.text(((W - tw) / 2, H - 300), txt, font=fx, fill=GOLD,
               stroke_width=4, stroke_fill=(0, 0, 0))

    path = os.path.join(TMP, f"ov{i}.png")
    img.save(path)
    return path


def run(cmd):
    subprocess.run(cmd, check=True)


def build_scene(i, pid, dur, title, sub, accent, kind):
    src = download(pid)
    ov = overlay_png(i, title, sub, accent, kind)
    frames = int(round(dur * FPS))
    # Ken Burns: phóng nhẹ, xen kẽ zoom vào / zoom ra
    if i % 2 == 0:
        z = f"min(1.0+0.12*on/{frames},1.12)"
    else:
        z = f"max(1.12-0.12*on/{frames},1.0)"
    vf_img = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
              f"crop={W*2}:{H*2},"
              f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
              f"d={frames}:s={W}x{H}:fps={FPS}")
    out = os.path.join(TMP, f"scene{i}.mp4")
    fc = (f"[0:v]{vf_img}[bg];"
          f"[1:v]format=rgba,fade=t=in:st=0.25:d=0.5:alpha=1[ov];"
          f"[bg][ov]overlay=0:0:shortest=1,format=yuv420p[v]")
    run(["ffmpeg", "-loglevel", "error", "-y",
         "-i", src, "-loop", "1", "-t", str(dur), "-i", ov,
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur),
         "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         out])
    return out


def main():
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    clips = [build_scene(i, *s) for i, s in enumerate(SCENES)]
    durs = [s[1] for s in SCENES]

    inputs, parts = [], []
    for c in clips:
        inputs += ["-i", c]
    prev, offset = "[0:v]", 0.0
    for k in range(1, len(clips)):
        offset += durs[k - 1] - XF
        lab = f"[x{k}]"
        trans = "fade" if k % 2 else "slideleft"
        parts.append(f"{prev}[{k}:v]xfade=transition={trans}:duration={XF}:offset={offset:.2f}{lab}")
        prev = lab
    total = sum(durs) - XF * (len(clips) - 1)
    parts.append(f"{prev}fade=t=out:st={total-0.6:.2f}:d=0.6,format=yuv420p[v]")

    run(["ffmpeg", "-loglevel", "error", "-y", *inputs,
         "-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
         "-filter_complex", ";".join(parts),
         "-map", "[v]", "-map", f"{len(clips)}:a",
         "-c:v", "libx264", "-preset", "medium", "-crf", "21",
         "-c:a", "aac", "-shortest", "-movflags", "+faststart", OUT])
    print(f"OK: {OUT} ({total:.1f}s)")


if __name__ == "__main__":
    main()
