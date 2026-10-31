"""Measure the v13 reference sheet into a numeric contract.

Reads reference/style_v13_ref.png, splits the sheet into its three panels
(front / three-quarter / top), segments each panel into colour families
(cream, mint, orange, charcoal, glow), and writes the bounding boxes plus the
derived proportion ratios to reference/style_v13_ref_contract.json.

Usage:
    python qa_v2/v13_ref_contract.py [--ref PATH] [--out PATH]
"""

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image


def to_hsv(rgb):
    """rgb: float array (...,3) in 0..1 -> h(deg) s v arrays."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(axis=-1)
    mn = rgb.min(axis=-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rm = m & (mx == r)
    gm = m & (mx == g) & ~rm
    bm = m & (mx == b) & ~rm & ~gm
    with np.errstate(invalid="ignore", divide="ignore"):
        h[rm] = (60 * ((g[rm] - b[rm]) / d[rm])) % 360
        h[gm] = 60 * ((b[gm] - r[gm]) / d[gm]) + 120
        h[bm] = 60 * ((r[bm] - g[bm]) / d[bm]) + 240
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0.0)
    return h, s, mx


def bbox_of(mask):
    if not mask.any():
        return None
    ys, xs = np.nonzero(mask)
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def wh(bb):
    if bb is None:
        return (0, 0)
    return (bb[2] - bb[0] + 1, bb[3] - bb[1] + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="reference/style_v13_ref.png")
    ap.add_argument("--out", default="reference/style_v13_ref_contract.json")
    args = ap.parse_args()

    img = Image.open(args.ref).convert("RGB")
    W, H = img.size
    a = np.asarray(img).astype(np.float32) / 255.0
    h, s, v = to_hsv(a)

    # ---- background: the sheet sits on a smooth light-grey gradient, so a
    #      distance-to-one-colour test flags the whole backdrop. The objects are
    #      either chromatic (cream/mint/orange) or dark (charcoal base/bezel),
    #      while the backdrop is desaturated and bright: use that instead.
    fg = (s > 0.06) | (v < 0.55)

    # ---- split the sheet into panels by empty columns
    colsum = fg.sum(axis=0)
    occupied = colsum > max(3, H * 0.002)
    panels = []
    x = 0
    while x < W:
        if occupied[x]:
            x0 = x
            while x < W and occupied[x]:
                x += 1
            if x - x0 > W * 0.05:      # ignore slivers such as the watermark
                panels.append((x0, x - 1))
        else:
            x += 1

    sheet = {
        "ref": os.path.abspath(args.ref),
        "size": [W, H],
        
        "panel_count": len(panels),
        "panels": [],
    }

    # ---- colour families (hue windows tuned from the p30/p50/p70 sampling)
    def family(name, hmin, hmax, smin, smax, vmin, vmax, wrap=False):
        if wrap:
            hm = (h >= hmin) | (h <= hmax)
        else:
            hm = (h >= hmin) & (h <= hmax)
        return hm & (s >= smin) & (s <= smax) & (v >= vmin) & (v <= vmax)

    FAMILIES = {
        "cream":    family("cream", 25, 60, 0.05, 0.30, 0.55, 1.00),
        "mint":     family("mint", 130, 190, 0.06, 0.45, 0.20, 0.95),
        "orange":   family("orange", 8, 40, 0.40, 1.00, 0.20, 0.95),
        "charcoal": (s < 0.35) & (v < 0.42),
        "glow":     family("glow", 165, 195, 0.35, 1.00, 0.70, 1.00),
    }

    for idx, (x0, x1) in enumerate(panels):
        pw = x1 - x0 + 1
        sub_fg = fg[:, x0:x1 + 1]
        bb = bbox_of(sub_fg)
        panel = {
            "index": idx,
            "x_range": [int(x0), int(x1)],
            "width": int(pw),
            "foreground_bbox": bb,
            "foreground_wh": list(wh(bb)),
            "families": {},
        }
        for fname, fmask in FAMILIES.items():
            m = np.zeros_like(sub_fg)
            m[:, :] = fmask[:, x0:x1 + 1] & sub_fg
            fbb = bbox_of(m)
            fw, fh = wh(fbb)
            panel["families"][fname] = {
                "pixels": int(m.sum()),
                "bbox": fbb,
                "wh": [fw, fh],
                "coverage_of_panel": round(float(m.sum()) / max(1, int(sub_fg.sum())), 4),
            }
        sheet["panels"].append(panel)

    # ---- contract ratios, taken from the FRONT panel (index 0)
    #      Per-family bboxes are not enough: the cream mask also contains the
    #      arm and the hopper, so the whole-sheet cream bbox is not the body.
    #      Isolate the body as the widest column band whose silhouette is
    #      solid top-to-bottom, then measure the appendages relative to it.
    ratios = {}
    if sheet["panels"]:
        x0, x1 = panels[0]
        sub = fg[:, x0:x1 + 1]
        solid = np.zeros_like(sub)
        for fmask in FAMILIES.values():
            solid |= (fmask[:, x0:x1 + 1] & sub)
        col_h = solid.sum(axis=0)

        # ---- body rectangle -------------------------------------------------
        # Silhouette methods cannot isolate the body here: the arm and the chute
        # are attached to it with visible shading seams but no background gap,
        # and the hopper sits directly on top. The body rectangle is therefore
        # seeded by hand-read coordinates and then REFINED by searching for the
        # strongest luminance gradient within +-40 px of each seeded edge. The
        # seed and the refined value are both recorded so the refinement is
        # auditable rather than a rubber stamp.
        gray = a.mean(axis=-1)
        gx = np.abs(np.diff(gray, axis=1))       # vertical edges
        gy = np.abs(np.diff(gray, axis=0))       # horizontal edges
        gxs = gx[:, x0:x1 + 1]
        gys = gy[:, x0:x1 + 1]

        SEED = {"left": 110, "right": 420, "top": 355, "bottom": 812}
        REFI = 40

        def refine_col(seed, lo, hi, row_slice):
            lo = max(0, max(lo, seed - REFI))
            hi = min(gxs.shape[1] - 1, min(hi, seed + REFI))
            if hi <= lo:
                return int(seed), 0.0
            prof = gxs[row_slice, lo:hi + 1].mean(axis=0)
            return int(lo + int(prof.argmax())), float(prof.max())

        def refine_row(seed, lo, hi, col_slice):
            lo = max(0, max(lo, seed - REFI))
            hi = min(gys.shape[0] - 1, min(hi, seed + REFI))
            if hi <= lo:
                return int(seed), 0.0
            prof = gys[lo:hi + 1, col_slice].mean(axis=1)
            return int(lo + int(prof.argmax())), float(prof.max())

        vband = slice(SEED["top"] + 40, SEED["bottom"] - 40)
        l_edge, l_score = refine_col(SEED["left"], 40, SEED["left"] + REFI, vband)
        r_edge, r_score = refine_col(SEED["right"], SEED["right"] - REFI, gxs.shape[1] - 1, vband)
        hband = slice(l_edge + 30, r_edge - 30)
        t_edge, t_score = refine_row(SEED["top"], 250, SEED["top"] + REFI, hband)
        b_edge, b_score = refine_row(SEED["bottom"], SEED["bottom"] - REFI, 900, hband)

        body_x0, body_x1 = l_edge, r_edge
        body_top, body_bot = t_edge, b_edge
        body_w = body_x1 - body_x0 + 1
        body_h = body_bot - body_top + 1

        glow_bb = sheet["panels"][0]["families"]["glow"]["bbox"]
        win_w = glow_bb[2] - glow_bb[0] + 1 if glow_bb else 0
        win_h = glow_bb[3] - glow_bb[1] + 1 if glow_bb else 0

        # hopper: solid strictly above the body top, inside the body's columns
        above = solid.copy()
        above[body_top:, :] = False
        abb = bbox_of(above[:, body_x0:body_x1 + 1])
        hop_w = (abb[2] - abb[0] + 1) if abb else 0
        hop_h = (abb[3] - abb[1] + 1) if abb else 0

        # chute: solid right of the body edge, between body top and bottom
        right = solid.copy()
        right[:, :body_x1 + 1] = False
        rbb = bbox_of(right[body_top:body_bot + 1, :])
        chute_w = (rbb[2] - rbb[0] + 1) if rbb else 0

        # base: charcoal rows below the body bottom
        char = FAMILIES["charcoal"][:, x0:x1 + 1] & sub
        below = char.copy()
        below[:body_bot - 2, :] = False
        bbb = bbox_of(below)
        base_h = (bbb[3] - bbb[1] + 1) if bbb else 0

        body = {
            "x_range": [int(body_x0), int(body_x1)],
            "y_range": [int(body_top), int(body_bot)],
            "w": int(body_w),
            "h": int(body_h),
        }
        if body_w and body_h:
            ratios["body_w_to_h"] = round(body_w / body_h, 4)
            ratios["window_w_to_body_w"] = round(win_w / body_w, 4)
            ratios["window_h_to_body_h"] = round(win_h / body_h, 4)
            ratios["hopper_dia_to_body_w"] = round(hop_w / body_w, 4)
            ratios["chute_len_to_body_w"] = round(chute_w / body_w, 4)
        if win_w:
            ratios["window_h_to_w"] = round(win_h / win_w, 4)
        if base_h and body_h:
            ratios["base_h_to_body_h"] = round(base_h / body_h, 4)
        ratios["body_px"] = body
        ratios["window_px"] = {"w": int(win_w), "h": int(win_h), "bbox": glow_bb}
        ratios["hopper_px"] = {"w": int(hop_w), "h": int(hop_h)}
        ratios["chute_px"] = {"w": int(chute_w)}
        ratios["body_edge_calibration"] = {
            "note": "body rectangle seeded by hand-read coordinates, then refined "
                    "to the strongest luminance gradient within +-40 px of each seed",
            "seed": SEED,
            "refined": body,
            "edge_gradient_strength": {
                "left": round(l_score, 5),
                "right": round(r_score, 5),
                "top": round(t_score, 5),
                "bottom": round(b_score, 5),
            },
            "panel_local_x": True,
            "y_is_absolute": True,
        }
    sheet["contract_ratios"] = ratios

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(sheet, fh, indent=2)

    print("PANELS %d -> %s" % (len(panels), panels))
    for p in sheet["panels"]:
        print("panel %d  fg=%s  " % (p["index"], p["foreground_wh"]))
        for k, val in p["families"].items():
            print("   %-9s px=%-8d bb=%-24s wh=%s" %
                  (k, val["pixels"], str(val["bbox"]), val["wh"]))
    print("RATIOS %s" % json.dumps(ratios, indent=2))
    print("WROTE %s" % os.path.abspath(args.out))


if __name__ == "__main__":
    sys.exit(main())


