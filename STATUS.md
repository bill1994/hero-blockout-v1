# STATUS — hero-blockout-v1 / v13 style pass

**Last updated:** 2026-11-02 (after stage P3f — reference pass 3: top mint skin, window resized, fingers thickened)
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
| **v13 P3b** | **`hero_animation_v13_p3b.blend` + `.glb`** | **hand rebuilt as a three-finger claw, floating lines removed, GLB re-exported, animation QA sheet done** |
| **v13 P3c** | **`hero_animation_v13_p3c.blend`** | reference pass 2, geometry only: arm rebuilt as a ball-and-tube chain with seam rings, hopper chunkier, window slimmed, body bevel 0.05, plinth gap closed, two buttons added, three front lights shrunk |
| **v13 P3d** | **`hero_animation_v13_p3d.blend`** | zero-risk finishing: feet dug out of the plinth, hopper throat mint collar, button ring seats, wrist amber cuff, tilted label decal |
| **v13 P3e** | **`hero_animation_v13_p3e.blend`** | outlet pass: rail narrowed to y ±0.42, `P1_ChuteSeat` rebuilt as a collar, `Outlet_Flap` re-authored as a flush cream hatch, plinth overhang trimmed, four reference-absent light meshes hidden |
| **v13 P3f (current)** | **`hero_animation_v13_p3f.blend`** | **reference pass 3: top mint is now a conformal skin wrapping the shoulders, window widened to 0.5421 and heightened, side mint strips raised to meet the skin, `Arm_Mount` creamed, fingers thickened 1.12× as tubes. No GLB yet — re-export from this file.** |

`hero_animation_v13_p3b.glb` is the newest GLB deliverable: 1,094,460 B, 76 meshes, 83 nodes,
15 materials, 18 animations, 21,802 triangles, images/textures/samplers all 0. **It predates
P3c, P3d, P3e and P3f**, so it does not contain the rebuilt arm, the hopper rework, the outlet
pass, the top skin or the resized window — re-export from `hero_animation_v13_p3f.blend` before
shipping anything.
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
| animation | 39 actions, 149 fcurves, 3,345 keys on P3a; **37 / 147 / 3,331 from P3b onward** (unchanged by P3c), loop endpoints all 0, f1 vs f327 `matrix_world` of all 93 objects identical | `qa_v2/v13_baseline_audit.py` |
| grab contact | **current (P3f): f31 0.00557/0.01118, f43 same, f147 0.01267/0.01492, f155 0.40271/0.45016, overlap 0** — P3b..P3e were f31 0.01148/0.01432, f147 0.01808/0.02085, f155 0.40630/0.45380; the P3f tightening is the 1.12× finger thickening, still well clear of the 0.002 floor | `qa_v2/v13_grab_gate.py` |
| triangle budget | 20,646 on P3a; 22,650 on P3b; 23,854 on P3c; 23,442 on P3d; 23,322 on P3e; **23,540 from P3f** of 25,000 (22,764 of them visible — the four hidden light meshes account for the rest) | `v13_baseline_audit.py` |

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

P3b and P3c are the two stages with no script. Both were authored live through the Blender
MCP bridge (port 9876) under the project rule that those stages run through MCP only. Every
parameter is recorded in `BUILD_NOTES.md` under "v13 P3b" and "v13 P3c", so the scripts can be
written from them, but **neither stage can currently be replayed from the P3a asset** the way
the earlier stages can.

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
3. **Remaining shape deltas against the reference after P3c**, all measured, none of them may
   touch the animation:
   - **The chute is the big one.** `Machine_Chute` is 2.24 long = 1.24 of body width; the
     reference measures 0.677. It cannot be shortened: `ProductAction.001_V2` drives the
     product from x 1.36 to 5.9 along that surface over f232..f289 and the part is parented
     to the keyframed empty `Machine_OutputChute`. P3e narrowed the rail to y ±0.42 and
     rebuilt `P1_ChuteSeat` as a 0.55-tall collar, so it now reads as a scoop plus a slim
     tongue; a downward raycast proved the cream shell carries the product on **0 of 57**
     RESTING+ARC frames (amber floor to xc 2.09, dark rail from xc 2.22), so the shell is
     decorative and only the tongue is structural.
   - `Outlet_Flap` was re-authored in P3e as a flush cream hatch (scale baked to 1, vertices
     rebuilt, amber -> `MAT_Body`); the −30° visor pose is gone. Its action still swings it
     out over f227..f255.
   - Window cavity is still light grey behind pale nebula spheres; the reference is a dark
     teal cavity with a diffuse nebula. Material change, deliberately deferred. The window
     *geometry* is now at reference proportion: `Machine_WindowGlow` is 0.9757 wide = **0.5421
     of body width, an exact match**; height 1.2656 = 0.7032 of body height against the
     reference's 0.6158, so `window_h_to_w` lands on 1.2972 against the reference's 1.5528.
     That last gap is unreachable: the reference's own three window numbers are mutually
     inconsistent (0.5421 × 1.5528 = 0.8416 ≠ 0.6158) and the button row plus the top bevel
     cap the achievable height at about 1.33.
   - The mint top is now a conformal skin (`P3f_TopSkin`, rebuilt from the body's evaluated
     top and shoulder faces, offset 0.0025 along the normals) that wraps both shoulders, and
     `P1_MintStrip_L/R` were raised to z 1.845 to meet it — so the mint reads as one continuous
     band instead of a plate on a box. It is too glossy under the QA key light; roughness is a
     material value and stays deferred.
   - Fingers are round tubes, thickened 1.12× along their bend by a PCA split (axial component
     untouched, perpendicular component scaled). The user ruled that round tubes read better
     than the reference's flat leaves, so the leaf rebuild is cancelled.
   - Four feet exist (`Machine_Feet`, exposed 0.08 below the plinth since P3d); the mint side
     panel is still a thin strip rather than the reference's large rounded panel.
   - `Machine_Light_01/02/03` and `Machine_LightStrip` do not exist in the reference and were
     hidden in P3e rather than deleted (data + actions kept for a later FX pass). Any GLB
     export must use `use_visible=True` or they come back.
   - body W:H 1.00 vs the reference's 0.73 (the section 12 Q1 accepted compromise).
4. **Lighting is now the weakest link, not geometry.** `Cam_Hero` plus two suns
   (`SUN_Hero` 3.0, `FILL_Hero` 0.8) with a 0.051 world is not the reference's studio look —
   the machine renders flat and dark under it while the shape reads well under the `QA_*`
   rig. Reverse-engineering the reference's soft key from upper left + large fill + seamless
   grey backdrop + contact shadow was ranked as a top lever in the design doc and is still
   untouched.
5. **Re-export the GLB from `hero_animation_v13_p3f.blend`** (`export_apply=True`,
   `use_visible=True` because `Machine_Light_01/02/03` and `Machine_LightStrip` are hidden and
   absent from the reference, then delete the 5 scaffolding cutters/proxies first). The
   existing `hero_animation_v13_p3b.glb` predates P3c…P3f and does not contain any of it.
6. **Delivery checklist**: `.blend` + `.glb` + `BUILD_NOTES.md` stage section + a final
   side-by-side four-view against `reference/style_v13_ref.png` at delivery framing.

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
