# STATUS — hero-blockout-v1 / v13 style pass

**Last updated:** 2026-11-01 (after commit `12e43ab`, stage P3a)
**Branch:** `main`. Everything below is committed. Remote work should continue from `main`.

Read `BUILD_NOTES.md` for the measured detail behind every claim here. This file is the
short version: where the asset is, what is proven, what is left, and how to run each
check yourself.

---

## 1. Where the asset is

| stage | file | state |
|---|---|---|
| v12 | `hero_animation_v12_style.blend` | pre-v13 baseline, untouched |
| v13 P0 | `hero_animation_v13_soft.blend` | hygiene pass only (materials, loop closure, re-seat ornaments) |
| v13 P1 | `hero_animation_v13_p1.blend` | shell 2.32 → 1.80, junctions, mint bands, palette, window 0.64 |
| v13 P2 | `hero_animation_v13_p2.blend` + `.glb` | window rebuilt, emissive nebula, GLB verified |
| **v13 P3a (current)** | **`hero_animation_v13_p3.blend`** | grab gate, chute split, hopper bowl |

`hero_animation_v13_p3.glb` does **not** exist yet — the GLB was last exported at P2 and
must be re-exported once the claw work lands.

## 2. What the plan wanted vs what is done

| plan stage | status |
|---|---|
| P0 audit fixes (D1–D3, Q4 loop closure) | done, verified |
| P1 shell round + width 1.80 + three junctions | done |
| P1 palette to section 5.1 | done (values set from measured p50 midtones) |
| P1 window ~0.64 | done, then corrected in P2 to the measured 0.5421 (see below) |
| P2 window shape + nebula + GLB parity | done |
| P3 grab criterion pinned before claw work | done |
| P3 hopper bowl | done |
| P3 chute scoop + rail | done |
| **P3 claw (rounded pads + fixed third finger)** | **not started** |
| final GLB export + animation QA sheet | not started |

### two places where the design doc contradicts itself (both decided, both recorded)

1. **Window width.** Section 6 P1 says ~0.64 of body width; section 4.3 measures the
   reference at 0.5421. 4.3 is the scripted measurement, so P2 rebuilt the opening to
   **0.5467 x 0.6200**. The 1.5528 window aspect in 4.3 is not reproducible on this body
   at all — it only holds because the reference machine is 0.73 W:H and this one is 1.00
   (section 12 Q1's accepted compromise).
2. **Hopper throat.** Section 12 Q1 asks whether the ball still passes the hopper mouth.
   There is no mouth: measured, the hopper is a closed shell and the orb **rests on a
   solid pedestal whose top face is z 2.35**. Nothing shrinks the hopper; section 9's
   "ball jams" risk is void.

## 3. Verified invariants (frozen — do not let these drift)

| quantity | value | how it is checked |
|---|---|---|
| body width / height | 1.8000 / 1.8000, x ±0.9000 | `qa_v2/v13_p1_preflight.py` |
| arm root | `Arm_Base` min x = **-1.864** | same |
| chute mouth | `Machine_Chute` min x = **1.160** | same |
| chute floor / support plane | **z 0.705** | `qa_v2/v13_product_path_gate.py` |
| orb rest | pedestal top **z 2.35**, orb centre (0,0,2.6), r 0.25 | axis ray in `v13_p3_chute_hopper.py` report |
| animation | 39 actions, 149 fcurves, 3,345 keys, loop endpoints all 0 | `qa_v2/v13_baseline_audit.py` |
| grab contact | f31 0.01799/0.00614, f43 same, f147 0.02555/0.02348, f155 0.41537/0.47581 | `qa_v2/v13_grab_gate.py` |
| triangle budget | 20,646 of 25,000 | `v13_baseline_audit.py` |

## 4. Gates and how to run them

Blender used throughout: `G:\Blender\blender-5.4.0-alpha\blender.exe` (machine-specific —
change the path on another machine; the asset was written by 5.4, opening it in 5.3 warns
about data loss).

```bat
set BL=C:\path\to\blender.exe
set A=hero_animation_v13_p3.blend

:: animation integrity, loop closure, grab contact, poly budget
"%BL%" --background %A% --python qa_v2/v13_baseline_audit.py -- --out qa_v2/x_audit.json

:: product support + fall (the gate the plan was missing)
"%BL%" --background %A% --python qa_v2/v13_product_path_gate.py -- --out qa_v2/x_gate.json

:: hard-surface intersection (product vs shell / chute / junction pieces)
"%BL%" --background %A% --python qa_v2/v13_penetration_check.py -- --out qa_v2/x_pen.json

:: grab contact, judged against the pinned bands
"%BL%" --background %A% --python qa_v2/v13_grab_gate.py -- --out qa_v2/x_grab.json

:: frozen anchors, hopper, window ratios
"%BL%" --background %A% --python qa_v2/v13_p1_preflight.py -- --out qa_v2/x_pre.json

:: four orthographic views (AgX; Standard used to clip the cream to white)
"%BL%" --background %A% --python qa_v2/v13_p0_render.py -- --outdir review/v13 --prefix x
```

Gates exit non-zero on FAIL (product-path uses 3, intersection 3, grab 3), so they can be
wired into CI as-is.

Palette sampling and the reference contact sheet run on plain Python + Pillow, not
Blender:

```bat
python qa_v2/v13_p1_review.py --palette review/v13/p3_front.png ^
    --sheet review/v13/contact.png --panels review/v13/p3_front.png,review/v13/p3_right.png,review/v13/p3_top.png
```

## 5. Pipeline order (running these twice is NOT safe)

The stage scripts mutate the file they are given. Run them in this order from the P0
asset, in sequence, each on the output of the previous:

```
v13_p1a_shell.py  ->  v13_p1b_dress.py  ->  v13_p1c_details.py  ->  v13_p2_window.py
                  ->  v13_p3_chute_hopper.py  ->  (P3b claw, to be written)
```

`v13_p1_seat_contact.py` is idempotent-ish and must be re-run **after any change to the
chute or body geometry**, because it re-derives the product's contact height from the
surface that is actually there. It only ever raises, never lowers.

## 6. What is next (in order)

1. **Claw (P3b).** `Arm_Finger_L/R` meshes → rounded chunky pads; add a third fixed finger
   on the wrist (no action). Rotation keys, origins and parenting must not move. Judge with
   `v13_grab_gate.py` — it fails on finger/orb face overlap, so a pad that grips by
   penetrating is rejected even if the distance looks fine.
2. **Re-export the GLB** from the finished blend
   (`export_apply=True`) and re-run the texture check — the P2 rule is hard: images 0,
   textures 0, samplers 0.
3. **Animation QA contact sheet** for the delivered frame rate, plus a final four-view
   against `reference/style_v13_ref.png`.
4. **Delivery checklist**: `.blend` + `.glb` + `BUILD_NOTES.md` stage section.

## 7. Tool caveats worth knowing before you trust a number

- **QA render exposure.** `v13_p0_render.py` used `Standard` view transform, which blew the
  cream to #FFF (25.8% of the front view's subject pixels). It now defaults to AgX. Any
  colour verdict made from renders produced before that change is void.
- **Stale depsgraph in `--background`.** `object.matrix_world` is not refreshed after
  `frame_set`; always read `obj.evaluated_get(dg).matrix_world`. And when measuring polygons,
  measure at a frame where the object is visible — the poly budget used to be read at f155
  where `Product` is scaled to 0.001, and its bevel was skipped, undercounting by 96 tris.
- **Welded seams + bevel = self-intersecting geometry.** The rebuilt chute welded three
  boxes at coplanar seams; the existing bevel modifier then produced self-intersecting
  geometry and every overlap test lied by 7 frames. Loose parts, walls sunk 5 mm into the
  floor, fixed it. Do not "fix" the intersection gate by triangulating it — that made a
  known-clean file report 27 frames.
- **`BVHTree.FromObject` ignores the parent chain**, so pieces parented to the body are
  compared at the wrong place. The gate builds world-space trees instead.
- **Building meshes in world coordinates for a parented object** silently displaces it
  (this moved the window cutter and stopped the outlet cutting). Build in local space via
  `matrix_world.inverted()`.

## 8. Open questions for the user

- The claw is the last visual gap; the reference's hand is a chunky three-finger claw with
  an orange cuff, and the current one is a thin pipe with oversized hoops.
- Body W:H stays at 1.00 against the reference's 0.73 — accepted in section 12 Q1, not
  revisited since.
