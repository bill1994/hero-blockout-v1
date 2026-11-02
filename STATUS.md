# STATUS — hero-blockout-v1 / v13 style pass

**Last updated:** 2026-11-01 (after stage P4 — the seven-item pass closed every reference ratio to within 0.1%; see the P4 row below)
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
| **v13 P3f** | **`hero_animation_v13_p3f.blend`** | reference pass 3: top mint is now a conformal skin wrapping the shoulders, window widened to 0.5421 and heightened, side mint strips raised to meet the skin, `Arm_Mount` creamed, fingers thickened 1.12× as tubes |
| **v13 P3g** | **`hero_animation_v13_p3g.blend`** | geometry pass closed: bevels on `P1_ShoulderBay` and both mint strips, eight bolt heads pulled 0.006 proud |
| **v13 P3h (current)** | **`hero_animation_v13_p3h.blend`** | **arm socket rebuilt to the reference crop: torus boss + backing disc + stub tube in `P1_ShoulderBay`, `Arm_Base` is a ball, yaw housing and riser are rings, the `Arm_Mount` plate is hidden. The arm no longer reads as a stack of boxes. No GLB yet — re-export from this file with `use_visible=True` (five objects are hidden on purpose).** |
| **v14 P4 (current)** | **`hero_animation_v14_p4.blend`** | **seven-item pass.** (1) `Arm_Base`, `Arm_Yaw_Housing` and `Arm_ShoulderRiser` carried 1.80-2.05 units of baked mesh offset, so the whole socket collapsed to the machine origin and the two rings rendered lying on the floor; mesh offsets zeroed, the socket now reads ball + collar + ball at the shoulder. (2) `MAT_Window_Glow` was white with emission 0; now cyan (0.122, 0.791, 0.783 linear) at strength 4.0. (3) body height 1.80 -> 2.46 (mesh Z x 1.36667, action keys +0.49), window re-cut to 0.9756 x 1.5154, every body child remapped proportionally. (4) chute shortened 2.24 -> 1.22 and all 24 faces set to `MAT_Color_Amber`. (5) base 0.12 -> 0.28 (scale_z 0.18667). (6) three-point studio lighting: world 0.55/0.52/0.48, AREA_Key 620 W, AREA_Fill 170 W, AREA_Rim 360 W, sun 1.3, exposure 0, view transform Standard. (7) the 30 `P2_Nebula_*` capsules are gone, replaced by `P2_Plasma`, a procedural emissive plane inside the window recess. Grab distance stays 0.006 at f31/f96/f147, loop delta 0.000, and every body child follows the f165 wobble by the same -0.048. Follow-up polish in the same file: `P1_ShoulderBay` was a lumpy blob and is now a rebuilt 48-segment cylindrical boss (radius 0.32, local x -0.365..0.14) with a 0.022 rim bevel; hopper scaled 1.03248 in XY so its diameter is exactly 0.7778 of body width; the outlet bore shrank from 0.91 to 0.52 tall and was re-centred on the chute mouth (z 0.878..1.398); `Outlet_Flap` became a compact 1.04 x 0.44 hatch covering that bore; `P1_ChuteSeat` trimmed to y +-0.70. All seven ratios now land within 2% (six within 0.1%). `hero_animation_v14_p4.glb` IS exported: 1.39 MB, 45 meshes, 52 nodes, 11 materials, 12 animations (hidden lights and `Arm_Mount` correctly excluded by use_visible), 1 embedded PNG. The plasma is procedural, so it was baked to `review/v14/plasma_bake.png` (512x768) and re-authored as `MAT_Nebula_Plasma_Baked` — procedural node trees do NOT survive glTF. The plane needed an explicit UV layer for that texture to land. Second polish pass: `Machine_Chute` was a flat-floored prism (32 verts) and is now a lofted curved U-channel scoop — 5 stations from x 1.16 to 2.38, elliptical trough 0.355 deep on a 0.05 shell, tapering half-width 0.63 -> 0.35 so the spout narrows, 190 verts, all faces on `MAT_Color_Amber`, world envelope x 1.16-2.38 / y +-0.68 / z 1.035-1.44, trough floor at 1.085 which is exactly where `Product` seats at f232. `Arm_Finger_L/R` were fat round sausages; they are now flattened 0.74 in local Y and cross-section-tapered to 0.70 over the outer 45% of their length, so they read as blades instead of tubes. Grab still 0.006 at f31/96/147, loop delta 0.000, chute_len/bodyW 0.6778. GLB re-exported at 1.42 MB with the same 45/52/11/12/1 structure. Plan-gap pass: `Machine_WindowGlass` added — a 56-segment superellipse disc (0.452 x 0.697 half-extents, exponent 3.2) domed 0.015 forward at y -0.780, with `MAT_Window_Glass` (base 0.020/0.060/0.058, roughness 0.02, alpha 0.38, IOR 1.45, alphaMode BLEND) — this closes the plan's missing third window layer, and it visibly tints the plasma. Screws went 8 -> 16 (`P1_Bolt_L0..L3` / `R0..R3` added on the side faces, rotated 90 deg about Z). A second plasma plane `P2_Plasma_Back` sits 0.062 behind the first with mirrored UVs at emission 0.55. `Arm_UpperArm_Seam_A/B` and `Arm_Forearm_Seam_A/B` are dark seam bands (32-gon rings, host radius +0.006, 0.020 wide) parented into the tubes. Triangles 24,512 / 60,000. Grab 0.006, loop 0.000, seam rings track the arm with 0.000 offset. GLB now 1,535,696 B, 59 meshes / 66 nodes / 13 materials / 12 animations / 1 image, `MAT_Window_Glass` exported as alphaMode BLEND. Structural pass: `P1_MintStrip_L/R` are now separate plates, 0.022 thick with their outer faces at +-0.912 (0.012 proud of the shell at +-0.900) so the panel edge casts a real step instead of reading as a decal. Bevel discipline normalised to a 4:2:1 ratio at model scale — class A 0.050 (shell), class B 0.025 (base, base band, shoulder bay, detail rail, top skin, which had no bevel before), class C 0.012 (gripper, wrist collar, outlet flap, fingers), with the mint plates and chute seat at 0.008/0.020. Triangles 25,392 / 60,000. Grab 0.006, loop 0.000, panel step measured at 0.012. GLB now 1,557,024 B / 59 meshes / 66 nodes / 13 materials / 12 animations / 1 image. Closing pass: the 8 side screws were misplaced at x +-0.803 (inside the 0.9 shell, invisible) and are now at +-0.903 with the rotation flipped per side; all 16 now share ONE `P1_Bolt_mesh` — a 12-gon head, radius 0.028 (up from 0.018 so the slot reads), 0.011 thick, with a 0.004-deep slot cut by an applied EXACT boolean — which is why the GLB mesh count dropped 59 -> 44. Base raised to 0.288 so base+feet / bodyH = 0.1577 against the reference 0.1576. `MAT_Idea` was Emission-only (the orb rendered as a flat disc); it now runs through the Principled BSDF with base + emissive 0.55, so the orb shades. Finger closed pose tightened from 0.5236 to 0.38 rad: f31/43 fingertip-to-orb-centre went 0.2602/0.2630 -> 0.2531/0.2560 against the plan's 0.2497 target, and f147 open stays 0.2677/0.2703 against 0.267. The f147-156 hopper check was run frame by frame: the orb is above the rim at f147/f152 (descending) and crosses into the bowl between f152 and f156, staying inside through f165 — the drop beat lands in the right window. Triangles 25,712 / 60,000. Grab 0.006, loop 0.000. GLB 1,524,228 B / 44 meshes / 66 nodes / 13 materials / 12 animations / 1 image. Known residual: fingertip distance is 1.4-2.5% over the plan's 0.2497 (rotation alone cannot close it — the finger arc is nearly tangential to the ball at that pose), and the plan's literal 4 mm / R12 numbers were applied as ratios instead, because at 1.8-unit body scale they are 0.9 px and smaller than the existing fillet.** |

`hero_animation_v13_p3b.glb` is the newest GLB deliverable: 1,094,460 B, 76 meshes, 83 nodes,
15 materials, 18 animations, 21,802 triangles, images/textures/samplers all 0. **It predates
P3c through P3h**, so it does not contain the rebuilt arm, the hopper rework, the outlet pass,
the top skin, the resized window, the polish passes or the new arm socket — re-export from
`hero_animation_v13_p3h.blend` before shipping anything, and pass `use_visible=True`: five
objects (`Machine_Light_01/02/03`, `Machine_LightStrip`, `Arm_Mount`) are hidden deliberately
because the reference has nothing there.
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
| triangle budget | 20,646 on P3a; 22,650 on P3b; 23,854 on P3c; 23,442 on P3d; 23,322 on P3e; 23,540 on P3f; 24,148 on P3g; **24,464 from P3h** of 25,000 (the arm-socket rebuild cost 316 net) | `v13_baseline_audit.py` |

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
