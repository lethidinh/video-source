"""Animate the two people in source.jpg (head sway / nod / breathing) and
render a 5s 1920x1080 video.

Usage: python3 animate.py source.jpg mask.png out.mp4
mask.png: person segmentation (white = people), e.g. from rembg u2net_human_seg.
"""
import subprocess
import sys

import cv2
import numpy as np

SRC, MASK, OUT = sys.argv[1:4]
FPS, DUR = 30, 5.0
N = int(FPS * DUR)
W_OUT, H_OUT = 1920, 1080

img = cv2.imread(SRC)
H, W = img.shape[:2]
mask = cv2.imread(MASK, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
# fill holes (sunglasses etc.) so faces move as one piece
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((61, 61), np.uint8))

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def ellipse(cx, cy, ax, ay, sigma):
    e = np.zeros((H, W), np.float32)
    cv2.ellipse(e, (cx, cy), (ax, ay), 0, 0, 360, 1.0, -1)
    return cv2.GaussianBlur(e, (0, 0), sigma)


def smooth(m, sigma):
    return cv2.GaussianBlur(m, (0, 0), sigma)


# Per-person motion regions (head + hair/hat), softened so the surrounding
# background deforms smoothly instead of tearing.
man_head = smooth(np.maximum(mask, 0.35) * ellipse(605, 640, 250, 330, 1), 30) * ellipse(605, 640, 260, 340, 40)
woman_head = smooth(np.maximum(mask, 0.35) * ellipse(250, 790, 250, 230, 1), 30) * ellipse(250, 790, 260, 240, 40)
woman_hand = ellipse(25, 870, 70, 110, 25)
body = smooth(mask, 40) * np.clip((yy - 850) / 250, 0, 1)  # shoulders / torso


def rot_disp(px, py, ang_deg, tx=0.0, ty=0.0):
    a = np.deg2rad(ang_deg)
    c, s = np.cos(a), np.sin(a)
    dx, dy = xx - px, yy - py
    # inverse map: where to sample from
    sx = px + c * dx + s * dy - tx
    sy = py - s * dx + c * dy - ty
    return sx - xx, sy - yy


def ease(t):
    return 0.5 - 0.5 * np.cos(np.pi * np.clip(t, 0, 1))


ffmpeg = subprocess.Popen([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-filter_complex",
    f"[0:v]split[a][b];"
    f"[a]scale={W_OUT}:{H_OUT}:force_original_aspect_ratio=increase,crop={W_OUT}:{H_OUT},"
    f"gblur=sigma=30,eq=brightness=-0.08[bg];"
    f"[b]scale=-2:{H_OUT}[fg];"
    f"[bg][fg]overlay=(W-w)/2:0,fade=t=in:st=0:d=0.4,fade=t=out:st={DUR-0.4}:d=0.4,format=yuv420p[v]",
    "-map", "[v]", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
    "-movflags", "+faststart", OUT,
], stdin=subprocess.PIPE)

for i in range(N):
    t = i / FPS
    w = 2 * np.pi / DUR  # one full cycle over the clip -> seamless loop

    # Man: gentle head tilt side to side + small nod, pivot at neck
    m_ang = 2.2 * np.sin(w * t)
    m_dx, m_dy = rot_disp(610, 980, m_ang, tx=6 * np.sin(w * t), ty=-5 * np.sin(2 * w * t))

    # Woman: leans her head toward him and back, opposite phase, pivot at neck
    f_ang = -3.0 * np.sin(w * t + 0.9)
    f_dx, f_dy = rot_disp(300, 960, f_ang, tx=8 * np.sin(w * t + 0.9), ty=-6 * np.sin(2 * w * t + 0.5))

    # Woman's hand on the hat brim: small wave
    h_dx, h_dy = 0 * xx, (-10 * np.sin(2 * w * t)) * np.ones_like(yy)

    # Breathing: torso scales slightly around the bottom center
    b = 0.012 * np.sin(2 * w * t)
    b_dx = -(xx - W / 2) * b
    b_dy = -(yy - H) * b

    map_x = xx + man_head * m_dx + woman_head * f_dx + woman_hand * h_dx + body * b_dx
    map_y = yy + man_head * m_dy + woman_head * f_dy + woman_hand * h_dy + body * b_dy

    # slow push-in
    z = 1 + 0.06 * ease(t / DUR)
    map_x = W / 2 + (map_x - W / 2) / z
    map_y = H / 2 + (map_y - H / 2) / z

    frame = cv2.remap(img, map_x.astype(np.float32), map_y.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    ffmpeg.stdin.write(frame.tobytes())

ffmpeg.stdin.close()
ffmpeg.wait()
