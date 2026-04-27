"""Remove white / flat gray paper fill from PRISM logo; output transparent PNG."""
from __future__ import annotations

import sys
from collections import deque

try:
    from PIL import Image
except ImportError:
    print("Pillow required: pip install Pillow", file=sys.stderr)
    sys.exit(1)


def lum(r: int, g: int, b: int) -> float:
    return 0.299 * r + 0.587 * g + 0.114 * b


def similar(a: tuple[int, int, int], b: tuple[int, int, int], tol: int) -> bool:
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol and abs(a[2] - b[2]) <= tol


def flood_from_edges(
    w: int,
    h: int,
    get_rgb,
    *,
    color_tol: int,
    min_lum: int,
    max_chroma: int,
) -> list[list[bool]]:
    q: deque[tuple[int, int]] = deque()
    seen = [[False] * w for _ in range(h)]

    def try_push(x: int, y: int) -> None:
        if x < 0 or x >= w or y < 0 or y >= h or seen[y][x]:
            return
        r, g, b = get_rgb(x, y)
        if lum(r, g, b) < min_lum:
            return
        if max(r, g, b) - min(r, g, b) > max_chroma:
            return
        seen[y][x] = True
        q.append((x, y))

    for x in range(w):
        try_push(x, 0)
        try_push(x, h - 1)
    for y in range(h):
        try_push(0, y)
        try_push(w - 1, y)

    while q:
        x, y = q.popleft()
        r0, g0, b0 = get_rgb(x, y)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= w or ny < 0 or ny >= h or seen[ny][nx]:
                continue
            r, g, b = get_rgb(nx, ny)
            if not similar((r, g, b), (r0, g0, b0), color_tol):
                continue
            if lum(r, g, b) < min_lum - 25:
                continue
            if max(r, g, b) - min(r, g, b) > max_chroma + 12:
                continue
            seen[ny][nx] = True
            q.append((nx, ny))
    return seen


def is_flat_paper(r: int, g: int, b: int) -> bool:
    """Near-neutral bright pixels (off-white/gray: plate behind bars, not chroma)."""
    span = max(r, g, b) - min(r, g, b)
    l = lum(r, g, b)
    if span <= 20 and l >= 155:
        return True
    return False


def is_pale_cool_fog(r: int, g: int, b: int) -> bool:
    """Light blue/gray haze (lens/glow) — slightly blue, still low chrome."""
    span = max(r, g, b) - min(r, g, b)
    l = lum(r, g, b)
    if l < 130 or l > 250:
        return False
    if b < r and b < g:
        return False
    return span <= 40 and (b - r) >= 3 and (b - g) >= 0 and l >= 145


def process(path: str, out_path: str) -> None:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    px = img.load()

    def get_rgb(x: int, y: int) -> tuple[int, int, int]:
        r, g, b, _a = px[x, y]
        return (r, g, b)

    m_edge = flood_from_edges(w, h, get_rgb, color_tol=45, min_lum=152, max_chroma=50)
    x_icon = int(w * 0.64)

    out = Image.new("RGBA", (w, h))
    opx = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if m_edge[y][x]:
                opx[x, y] = (0, 0, 0, 0)
                continue
            if x < x_icon:
                if is_flat_paper(r, g, b) or is_pale_cool_fog(r, g, b):
                    opx[x, y] = (0, 0, 0, 0)
                    continue
            opx[x, y] = (r, g, b, a)
    out.save(out_path, "PNG")


if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "prism-logo-horizontal.png"
    outp = sys.argv[2] if len(sys.argv) > 2 else "prism-logo-horizontal.png"
    process(inp, outp)
    print("wrote", outp, flush=True)
