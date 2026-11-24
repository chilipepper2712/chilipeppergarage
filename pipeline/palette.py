"""Shared palette for every car: keeps the pixel look consistent across the lineup."""
import numpy as np

COLORS = {}
RAMPS = {
    "blue":  ["#081a45", "#10307a", "#1a4bb0", "#2d6be0", "#5c93f2", "#a8c8ff"],
    "red":   ["#3d0607", "#6e0d10", "#a31519", "#d42b2b", "#f05a4e", "#ffb0a0"],
    "white": ["#6c7178", "#9aa0a7", "#c3c8cd", "#dfe2e5", "#f1f3f5", "#ffffff"],
    "black": ["#08080a", "#121216", "#1c1d22", "#2a2b31", "#3e4048", "#6a6d76"],
    "glass": ["#081a20", "#0f2c35", "#17414d", "#235a68", "#3d8494"],
    "tyre":  ["#111113", "#1b1b1e", "#26262a", "#34343a"],
    "metal": ["#3a3d42", "#5d6168", "#878c94", "#b3b8bf", "#e2e6ea"],
}
SINGLE = {
    "black": "#121215", "plastic": "#24252a", "under": "#0d0d0f",
    "chrome": "#8c939c", "chrome_hi": "#eef2f6", "light_w": "#c9d3dc",
    "tail": "#7a0d10", "tail_hi": "#d3262b", "amber": "#e08a1c",
    "plate": "#e6e6de", "seam_blue": "#050f2c", "seam_red": "#2a0304",
    "seam_white": "#4a4e55", "seam_black": "#050506", "brake": "#4a4b52",
}

LIST = []
INDEX = {}
RAMP_IDX = {}


def _hex(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


for name, hs in RAMPS.items():
    RAMP_IDX[name] = []
    for i, h in enumerate(hs):
        INDEX[f"{name}{i}"] = len(LIST); RAMP_IDX[name].append(len(LIST)); LIST.append(_hex(h))
for name, h in SINGLE.items():
    INDEX[name] = len(LIST); LIST.append(_hex(h))
RGB = np.array(LIST, np.uint8)

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0


def ramp(name):
    return np.array(RAMP_IDX[name])


def dither(r, lum, bay, spread=0.9):
    n = len(r)
    pos = np.clip(lum, 0, 1) * (n - 1) + (bay - 0.5) * spread
    return r[np.clip(np.round(pos).astype(int), 0, n - 1)]


def dilate(img, it):
    """Grow islands outward (no wrap-around at texture borders)."""
    H, W = img.shape
    for _ in range(it):
        pad = np.pad(img, 1, constant_values=-1)
        out = img.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sh = pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]
            fill = (out < 0) & (sh >= 0)
            out[fill] = sh[fill]
        if (out == img).all(): break
        img = out
    return img


def to_rgb(img):
    out = np.zeros(img.shape + (3,), np.uint8)
    out[:] = (24, 24, 28)
    m = img >= 0
    out[m] = RGB[img[m]]
    return out
