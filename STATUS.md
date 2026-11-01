# STATUS — hero-blockout-v1 / v13 style pass

**Last updated:** 2026-11-01 (after stage P3b)
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
| v13 P3a | `hero_animation_v13_p3.blend` | grab gate, chute split, hopper bowl |
| **v13 P3b (current)** | **`hero_animation_v13_p3b.blend` + `.glb`** | **hand rebuilt as a three-finger claw, floating lines removed, GLB re-exported, animation QA sheet done** |

`hero_animation_v13_p3b.glb` is the current deliverable: 1,094,460 B, 76 meshes, 83 nodes,
15 materials, 18 animations, 21,802 triangles, images/textures/samplers all 0.
`hero_animation_v13_p3.glb` does not exist - the GLB skipped P3a entirely.

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
| **P3 claw (rounded pads + fixed third finger)** | **done - palm ellipsoid, three hooked fingers, wrist collar rebuilt** |
| final GLB export + animation QA sheet | done (P3b) |

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
| animation | 39 actions, 149 fcurves, 3,345 keys on P3a; **37 / 147 / 3,331 from P3b** (see below), loop endpoints all 0 | `qa_v2/v13_baseline_audit.py` |
| grab contact | f31 0.01799/0.00614, f43 same, f147 0.02555/0.02348, f155 0.41537/0.47581 - **these are the P3a numbers; since P3b they are f31 0.01148/0.01432, f147 0.01808/0.02085, f155 0.40630/0.45380, overlap 0** | `qa_v2/v13_grab_gate.py` |
| triangle budget | 20,646 on P3a; **22,650 from P3b** of 25,000 | `v13_baseline_audit.py` |

The 39 -> 37 action drop is **not a regression**: `MAT_Window_Noise1Action` and
`MAT_Window_Noise2Action` lost their nodes when P2 rebuilt the window, became zero-user
datablocks and were dropped on the next save-reload. Nothing evaluates them.

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
                  ->  v13_p3_chute_hopper.py  ->  (P3b claw: NO SCRIPT)
```

P3b is the one stage with no script. It was authored live through the Blender MCP bridge
(port 9876) under the project rule that this stage runs through MCP only. Every parameter is
recorded in `BUILD_NOTES.md` under "v13 P3b", so the script can be written from it, but
**P3b cannot currently be replayed from the P3a asset** the way the earlier stages can.

`v13_p1_seat_contact.py` is idempotent-ish and must be re-run **after any change to the
chute or body geometry**, because it re-derives the product's contact height from the
surface that is actually there. It only ever raises, never lowers.

## 6. What is next (in order)

1. **Write `qa_v2/v13_p3b_claw.py`** from the recorded parameters so the claw stage becomes
   replayable like the others. This is the only stage-script gap left.
2. **The claw cannot close around the orb.** The orb is r 0.25 with its centre 0.396 ahead of
   the wrist, so fingers reach its surface at x 0.146 and cannot meet in front of it without
   wrapping past x 0.579. The delivered ceiling is "three pads touching, palm cupped behind".
   Changing that means changing the orb radius, which the animation pins.
3. **Remaining shape deltas against the reference**, all measured, none of them may touch the
   animation: body W:H 1.00 vs the reference's 0.73 (accepted compromise), hopper neck still a
   straight cylinder while the reference has a short cream neck under the mint collar, base
   band still thin, and the arm still reads as a pipe with hoops rather than the reference's
   tapered tube.
4. **Delivery checklist**: `.blend` + `.glb` + `BUILD_NOTES.md` stage section. P3b has all
   three; what is left is a final side-by-side four-view against
   `reference/style_v13_ref.png` at delivery framing.

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
  `matrix_world.inverted()`. The claw is the sharpest case: `Arm_Finger_L/R` and
  `Arm_Gripper` all carry a non-identity `matrix_parent_inverse`, so wrist-space points have
  to be pushed through `obj.matrix_world.inverted() @ wrist.matrix_world` before they are
  written into the mesh.
- **Degenerate faces become NaN under Bevel, and NaN kills the glTF exporter.**
  `export_apply=True` fails with `ValueError: cannot convert float NaN to integer` at
  `io_scene_gltf2/blender/exp/export.py:515`. The raw mesh looks fine because `polygon.area`
  is only read after evaluation. Check the evaluated mesh: `Arm_Finger_L/R` had 15 NaN
  vertices each, grown from 16 zero-area tip-cap faces. `remove_doubles(1e-5)` +
  `dissolve_degenerate(1e-6)` fixes it; the grab gate does not notice, because you cannot
  grip with a degenerate face.

## 8. Open questions for the user

- **The claw is closed as far as geometry allows.** Reference wants a cage of three fingers
  around the orb; the orb (r 0.25, centre 0.396 ahead of the wrist) makes that impossible
  without moving the animation. Delivered: three hooked pads touching the orb, palm cupped
  behind. If a true cage is wanted, the orb radius or its distance from the wrist has to
  change - that is a user call, not a modelling one.
- **P3b has no stage script** (see section 5). Worth writing before anyone replays the
  pipeline.
- Body W:H stays at 1.00 against the reference's 0.73 — accepted in section 12 Q1, not
  revisited since.
