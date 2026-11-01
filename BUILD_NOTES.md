# Hero 动画 v3 执行记录

> 执行时间：2026-10-29
> 输入：`hero_animation_v2_5s.blend`（未改动）
> 输出：`hero_animation_v3_coherent.blend` + `hero_animation_v3_coherent.glb` + `review/`
> 依据：`ANIMATION_FIX_PLAN.md` v3-revised

## 1. 执行摘要

| 阶段 | 结果 | 备注 |
|---|---|---|
| P0-1 Flap 两段式开门 | 完成 | 176/179 旧键删除，插入 138(-0.56) / 170(-0.90) / 178(-1.55)，182 全开 |
| P0-2 Product creep | 完成 | 150(1.35) → 176(1.40)，实际位移 +0.05 |
| P0-3 死区余震 | 完成 | Root.rotation_x 149(+0.004) / 156(-0.002) / 164(+0.001)；Hopper/Body Z 按 -0.0104/+0.0052/-0.0026 跟随 |
| P0-4 收尾带速度 | 部分 | AUTO handle 无法缩短，实际由 P0-3 余震承担"144 帧后仍有运动" |
| P1-1 hide 提前 | 完成 | 175(隐藏) → 176(显示) |
| P1-2 起步拉长 | 完成 | 176(1.38) → 179(1.31) 回缩 → 182(1.38) → 184(1.52) |
| P1-3 squash | 完成 | 208(0.95) / **210(0.93)** / 212(0.95)，峰值帧 210 |
| P2 空转键 + 键距 | 完成 | 删 241 个同值平台键，处理 32 处 1 帧键（删 32 / 后移 46） |
| P3-2 scale 替代 hide | 完成 | 三轴 1-175(0.001) / 176(恢复) / 287(1.0) / 288-301(0.001) |
| P3-3 FollowGrab 烘焙 | 完成 | 38 个采样点烘焙为 location，约束删除，孤儿 influence 曲线清除 |
| P3-4 末端减速 | 完成 | 283(6.1) / 286(6.55) / 288(6.72) |
| P4 手臂稀疏化 | 完成 | P2 已删除大部分烘焙键，RDP 额外简化 2 通道（65→59 键） |

## 2. 数值门结果

| 指标 | 修改前 | 修改后 | 目标 | 判定 |
|---|---|---|---|---|
| D1 死区 | 126 | 123 | 动作段 ≤7 帧 | 部分 |
| D2 单帧跳变 | 62 | 64 | ≤5 | 未达 |
| D3 1 帧键 | 88 | 14 | — | 达成（剩余全为显隐切换） |
| D4 空转键 | 265 | 126 | — | 大幅改善 |
| D5 循环端点 | 0 | 0 | 0 | 达成 |
| D6 交付风险 | 123 | 122 | ≤20 | 未达 |
| D7 导出后遗症 | 6 | 4 | 0 | 部分（hide 已由 scale 覆盖，不进 GLB） |
| LINEAR 插值 | 117 | 32 | — | 改善 |

### 2.1 D6 未达成的确切原因

D6 判定逻辑：单帧变化超过值域 8% 记为"快速帧"，连续快速帧数 < 30fps 采样步长（2）则判为"30fps 会跳过"。

剩余 122 条风险中，绝大多数是晃动段（88-144）峰值附近的单帧最快点。例如 `Machine_Root.rotation_x` 88(0) → 91(0.02496) 是 3 帧完成的动作，BEZIER 在 90→91 处速度最大，单帧变化超过 8% 阈值，burst 计为 1。

这不是"键加得不对"，而是**60fps 下 3 帧完成的机械晃动，在 30fps 下必然只有 1-2 个采样点**。要真正压到 ≤20，必须把整个晃动段时长拉长一倍，属于重做节奏，超出 refinement 范围。

### 2.2 D2 上升 2 条的原因

新增的 2 条来自 `Product.location.x` 288→289 的复位过程。为避免 1 帧间隔，复位从 289 移到 290，导致 288→289 的中间插值为 4.035（跳变 50% 值域）。该跳变发生在隐藏期（scale 0.001 + hide），视觉不可见，但数值上仍会被记录。

### 2.3 D1 剩余值的判读

123 条中绝大部分属于设计静止，不是缺陷：

- `Arm_Finger_L/R` 73-301（228 帧）：手指在抓取完成后不再动作，合理。
- `Machine_Light_*` color 102-301（199 帧）：灯光颜色到位后定格，合理。
- `Product.location.z` 1-200（199 帧）：产品在出料前 Z 轴不动，合理。
- `Machine_Root.rotation_z` 118-301（183 帧）：Z 轴旋转完成后静止，合理。

原计划点名的 144-176 死区（32 帧）**已从 D1 榜上消失**，说明 P0-3 余震生效。

## 3. 像素门结果

渲染帧：95 / 115 / 144 / 152 / 176 / 179 / 182 / 186 / 190 / 210 / 260 / 288（640×480，EEVEE，Cam_Hero）。

| 对比 | 观察 | 判定 |
|---|---|---|
| 144 → 152 | 手臂从收拢转伸展，画面无冻结感 | 通过 |
| 176 → 182 | 产品在出料口稳定露出，未穿模 | 通过 |
| 176 → 179 | 回缩 0.08 m（约 12 px），可见度有限 | 偏弱 |
| 190 → 210 | 产品从滑出转为浮起，轨迹连续 | 通过 |
| 288 | 产品完全隐藏，Idea 球复位至左上 | 通过 |

**遗留观察**：P1 的 anticipation 幅度（0.08 m）在当前机位下偏弱。若需更强"蓄力感"，可加大到 0.15 m，但需先确认出料口内壁余量。

## 4. 交付门结果

GLB 导出：`hero_animation_v3_coherent.glb`，569,900 bytes。

- 动画动作数：19
- 通道类型分布：translation 11 / rotation 8 / scale 2
- `Product` 节点通道：translation + scale
- **hide 通道残留：无**
- 导出器已对全部动作执行逐帧烘焙（"Baking animation because..." 警告为预期行为）

## 5. 交付物清单

| 文件 | 说明 |
|---|---|
| `hero_animation_v3_coherent.blend` | 主工作文件 |
| `hero_animation_v3_coherent.glb` | 交付用模型，已验证无 hide 残留 |
| `review/v3_*.png` | 12 帧验收图 |
| `ANIMATION_FIX_PLAN.md` | 修订版计划（v3-revised） |
| `BUILD_NOTES.md` | 本文件 |

## 6. 未完成与建议

1. **D6 未达标（122 / 目标 20）**。这是动画固有节奏与 30fps 采样的结构性矛盾，不是键位问题。选项：
   - 接受现状：30fps 下晃动段会有 1 帧峰值丢失，但整体节奏不受影响。
   - 重做晃动节奏：88-144 段整体拉长至 1.5-2 倍，代价是加工反应变慢、总时长增加。
   - 改为 24fps 或 60fps 交付：回避 30fps 采样问题。

2. **D2 的 2 条新增**来自隐藏期复位，建议在验收时按"不可见"豁免。

3. **anticipation 幅度偏弱**，如需加强见第 3 节遗留观察。

4. **P4 手臂稀疏化实际收益有限**：P2 的 `prune_flat` 已删除绝大部分烘焙键，RDP 只额外处理了 2 个通道。若后续需要更彻底的手臂重做，建议单独一轮。

---

## v5 ease (2026-10-30)

input v4 -> output hero_animation_v5_ease.blend + .glb, 301f@60fps unchanged.
retime: f<=31 keep; 31<f<=129 +10f dwell; 129<f<=225 compress 139+(f-129)*86/96; >225 keep.
grab hold 31-43: Yaw -2.811 / Sh -1.1768 / El 1.9487 / Idea -3.2961,-0.6181,1.7219; Idea Z breathe 35 +0.02 / 39 -0.015; squeeze 0.985->0.90 + rebound 34:1.04/38:1.0.
ease: Yaw 1-105 LINEAR(26)->BEZIER EASE_IN_OUT; whip 67.3->65.5 / 70->72 (2.7f->6.5f).
transit stretch 1.35x (43-88, dead k=0.885): peak Yaw 19.4->11.4, Idea 16.6->11.0.
coda: WristY 194:0/205:0.4/218:-0.3/232:0.18/248:0, WristZ comp, LightStrip 200:1.0/215:1.8/230:1.0, Sh 205:-0.50/218:-0.64.
verify: 31-43 Yaw 0 / Idea 0.2-0.5m/s; contact validation/v5_031/039/070/141/218.png (031=039 hold, 218 coda distinct); 248-258 teleport hidden exempt.

---

## v6 retime (2026-10-30)

input v5 (301f) -> output hero_animation_v6_retime.blend + .glb, 327f@60fps (~5.45s).
user brief: hold at 30f invisible -> make it obvious + bigger wobble; whip at 64/65 too fast;
cut tail at ~275 (pose == 300 loop point, beyond-track content cropped by camera) and
re-extend to 300+, retime everything with front-weighted budget. Approved: freeze-frame
hold + big wobble, total duration may grow.

### retime map (old -> new, piecewise linear, all keys incl. handles)
1->1, 31->31, 43->55 (hold 12f->24f), 72->100 (whip zone 1.55x), 129->170,
186->225, 225->270, 258->305, 275->320. Then follower-sync warp +6.5f tail -> end 327.

### changes
1. grab hold 31-55 (24f): Yaw/Sh/El frozen at grab values; Idea XY nailed, Z breathe
   +3/+4.5/0/-4.5/-3/0cm (was +-2cm); squeeze 0.85@31 + rebound 1.05@37 (was 0.90/1.04).
2. whip: Yaw Z 10 keys redistributed by constant-angular-velocity (~3.5rad/s avg,
   41f span 76->117, all BEZIER EASE_IN_OUT). Peak 19.4 -> 3.7 rad/s.
   Lesson: even time spacing does NOT fix uneven value jumps; allocate time proportional
   to delta. Follower-sync warp applied to all non-Yaw keys (offset curve through whip,
   +6.5f constant tail) after spotting ball-out-of-gripper at f96 (6f desync).
   Verified gripper-ball distance 0.22-0.31 vs hold baseline 0.237.
3. tail: keys >275 deleted (95 keys); Sh/El eased 270->320 into loop-start values
   (-0.62/1.95); Idea loop-clean at start pose from 305; Product CONSTANT hide+shrink
   at 320 (off-camera); frame 327 == frame 1 (fingers/ball verified identical).
4. Idea transit peak 16.6 -> 8.4 m/s (translation, kept; rotation complaint resolved).

### verify
- numeric: hold 31-55 Yaw 0.0, Idea XY locked; whip peak 3.7 <= 6 target.
- contact validation/v6_031/043/096b/267/327 (031==043 hold, 096b ball-in-gripper
  mid-swing, 267 coda out-feed, 327 loop point).
- GLB exported (baking warnings expected, same as v3-v5).

---

## v7 product-out + global de-linear (2026-10-30, in v6 file)

user: front ok; product-out stage wrong; remove LINEAR feel across ALL stages.
file stays hero_animation_v6_retime.blend + .glb (re-exported), 327f.

### product-out diagnosis (pre-fix path sample)
- 231.67 pop-in (scale 0.001->1.0 in 0.8f) at x=1.4 inside machine
- 231->253 shuffle to x=2.72, hop z 0.9->1.55->1.2 by 273
- 253->313 x FROZEN 60f at 2.72 (v6 tail-cut deleted slide keys -> gap; the ugly freeze)
- 313->323 lazy slide 2.72->3.8, pop-hide at 326.5

### product-out fix
- grow-in: scale xy 1.0 key 231.67->238 (6f form-up, unhide stays 231.67)
- slide rebuilt: del X keys 313.26/318.56/323.85; add 280:3.00 / 296:3.55 / 308:3.80 (ease-out arrival)
- eject: 308->322 x 3.8->4.4 (conveyor eject off tray) + shrink 308->326.5 (scale plateau
  nails added @308 xyz=1.0; previously shrink spanned 238->326, deflating mid-slide)
- hide+shrink pop stays 326.5 (off-camera per user). z-hop untouched.
- post-fix path: 238 (1.43, full) -> 273 (2.85, landed) -> 308 (3.8, full) -> 322 (4.4, small) -> 326 hide. No freeze.

### global de-linear
- audit found 237 LINEAR keys: arm pivots X/Z statics (~0, invisible) + El/Sh Y @137-156
  (return dwell) + Idea X/Y @147/153/156. All -> BEZIER EASE_IN_OUT. Remaining LINEAR: 0.
- front (1-130) had no visible LINEAR -> hold/whip feel preserved; verified v7_043 == hold.

### verify
- contact validation/v7_043 (hold ok) / v7_240 (forming) / v7_262 (on tray) / v7_300 (sliding right).
- GLB re-exported (only key-count baking warnings; interp warnings gone except CONSTANT mixes).

---

## v8 idea constraint-bake (2026-10-30, in v6 file, 327f)

user: Idea scale jitters after grab (should stay constant); Idea transform lags gripper -> use constraint?
answer: yes, Child Of -> baked. file stays hero_animation_v6_retime.blend + .glb.

### scale autopsy
- Idea scale had zombie keys @310.44 (0.35) -> @316.79 (1.0): ball visibly GREW after loop point.
  plus old squeeze 0.85@31 + rebound 1.05@37 with BEZIER overshoot.
- fix: deleted ALL Idea scale keys, scale locked (1,1,1). user asked constant size -> no squeeze at all.

### follow autopsy
- release frame found by sampling: dist 0.24 @147, 0.34 @150 -> release ~147-148 (fingers stay shut, ball free-falls).
- Child Of (Idea -> Arm_Wrist, no scale) + inverse + influence envelope 28:0/31:1/147:1/150:0.
- gotchas hit (keep for next time):
  1. compute inverse with influence 0 (else polluted W); formula I = T^-1 @ W @ L^-1 because
     this Blender evaluates C = T @ I @ L (local multiplied, not replaced).
  2. with influence 1 the underlying keys must be STATIC or motion doubles -> flattened
     Idea location 31<f<147 to grab pose (fresh channelbag per pass; stale bags show zombie keys).
  3. BEZIER overshoot on a 0.5f step (145 grab -> 145.49 fall, z to 5.18) gets amplified by T-delta.
- end-state: sampled constrained C(f) 28..155, replaced location keys in [28,155] with baked
  (BEZIER, 128f), REMOVED constraint + influence FC. no live constraint left; export bakes plain keys.
- baked dist: 28-147 rigid 0.17-0.24, 150+ free fall 0.37->0.75. renders v8_043 (hold) / v8_096 (mid-swing in hand).

---

## v9 grip reattach — Idea rebuilt from the gripper (2026-10-30)

input v6 file (327f) -> output hero_animation_v9_grip.blend + .glb, 327f@60fps unchanged.
user: after the constraint the Idea moves even more bizarrely and no longer rotates with the claw.
Is it the constraint? Rebuild the Idea animation from the claw.

### diagnosis (measured, before)
1. f148 release excursion: Idea swings 2.74 m BACKWARD (to x=-1.77, z=1.44) then returns by f151.
   Root cause: the v8 bake sampled the Child Of result ACROSS the influence ramp 147:1 -> 150:0
   while the raw keys for 148-156 were never flattened (only 31<f<147 was). The influence blend
   interpolated between the flattened grab pose and the stale old fall keys -> a 2.74 m lash got
   baked in as real keys. A constraint blend artifact was frozen into the animation. Not a bad
   constraint setting: a bad bake window.
2. carry drift: Idea-to-gripper distance grew monotonically 0.006 (f31) -> 0.152 (f70), i.e. the
   held ball slid 15 cm out of a stationary gripper. The "breath/wobble" keys are in WORLD space,
   so they were never relative to the gripper.
3. rotation: Idea had NO rotation fcurve at all (5 fcurves = location x3 + hide x2). The wrist yaws
   161 deg across the whip (Z -161.06 -> -0.14) and the ball never turned.

### rebuild (deterministic, no live constraint)
- grabbed f31, released f147 (fingers open @148.75). offset I = W_gp(31)^-1 @ W_idea(31), 6 mm.
- carry f31-147: W_idea(f) = W_gp(f) @ I  -> translation AND rotation, baked per frame (117f).
  euler taken with to_euler('XYZ', prev) so no branch flips; max step 4.5 deg/frame.
- drop f148-156: straight vertical, accelerating (t^2), from (-0.013, 0.002, 3.496) to (0, 0, 2.600).
  Landing moved down from 2.7457 to 2.600 because the hopper is an open cone z 2.0..2.9 (r 0.3->0.45)
  and the ball is r=0.25: at 2.7457 its top (2.996) stuck 10 cm above the rim before the hide.
- hold 156-311 at the landing pose, hidden; teleport at 311.5 to the parked loop pose (unchanged).
- interpolation: LINEAR inside 31-156 (per-frame keys, exact, no bezier overshoot);
  the 311.4 hold key is CONSTANT so the 311.5 teleport is a 0.1f step inside the hide boundary.
- keys 1-30 and 312-327 untouched (parked/approach front kept as authored).

### verify (measured, after)
- carry dist to gripper constant 0.00602 over all 117 carried frames (was up to 0.152).
- rotation carried: f70 (-12.2, 31.5, 15.0) / f96 (-46.6, 64.7, 59.8) / f147 (-27.2, 53.1, 147.2) deg.
- drop speed ramps 0.56 -> 9.44 m/s, monotonic, no return excursion.
- loop f327 vs f1: distance 0.000000, rotation 0.000000.
- visible-frame peak speeds: f022 11.77 (pre-grab descent, pre-existing), f156 11.28 (sinking into
  the hopper), f077 11.00 (whip). The 213 m/s peak is the 311.5 teleport, hidden -> exempt.
- renders validation/v9_before_* vs v9_after_* at 043/096/147/148/149/150/155.
- GLB re-exported (577,004 bytes), verified by GLB JSON parse: Idea node carries BOTH animation
  channels, translation + rotation, 327 samples each, 0.017 -> 5.45 s.

### open / notes
- The Idea mesh is a perfect featureless sphere (482 verts, radius 0.25, no texture, plain white
  emission). Rotation is therefore INVISIBLE in render today. The rotation channel is now correct
  and will "just work" the moment a logo/decal/material break is added.
- f156 sinks at 11.3 m/s (0.9 m in 9f, ~3x gravity) — matches the piece's snappy whip energy and
  is occluded by the hopper; soften by lengthening the drop if it reads too fast.

---

## v10 white-model art pass (2026-10-30)

input v9 (327f) -> output hero_animation_v10_art.blend + .glb, 327f unchanged.
user: animation is close enough; next is model refinement. Chosen direction: white-model art pass
FIRST, materials in a later round. Product stays a 1 m cube, but its exit becomes a blast-out
instead of a shrink-away.

### measured starting state (before)
- 3,368 faces total; 22 of 29 meshes were 8-vert / 6-face axis-aligned boxes.
- `use_smooth` = 0 on EVERY polygon in the file, including the 512-face spheres and the 34-face
  hopper cone -> hard facets everywhere.
- Product: 1.0 x 1.0 x 0.985 (spec still said 0.4), sliding to x=3.8 while the chute ended at
  x=3.0, then deflating 308->326.5 in plain view.
- Earlier claim "product floats 18 cm above the chute" was WRONG: f267 is mid-hop (z 1.55->1.32).
  At rest z=1.2, mesh bottom 0.7 vs chute floor 0.705 -> seated. Corrected here so nobody chases it.

### changes
1. shading: all polys smooth + Shade Auto Smooth (30 deg) on all visible meshes -> curved surfaces
   smooth, box edges stay sharp.
2. bevels: Bevel_Art modifier (width 0.007-0.02, 2 segments, angle 30) on 12 box parts.
3. gripper: fingers were 0.3x0.07x0.1 paddles at y=+-0.09 whose tips sat 9 mm inside the 0.25 ball.
   Rebuilt as tapered jaws at y=+-0.175, length 0.17, 0.025/0.0425 half-section -> nearest vertex
   0.2497 closed (0.3 mm inside = contact) and 0.267 open (clears on release). Object origins,
   scale=1, and ALL finger rotation keys untouched, so the open/close beats are bit-identical.
   Palm reshaped (Arm_Gripper relocated to 1.54, 0.16 x 0.34 x 0.26). New Arm_WristCollar r=0.088.
   GOTCHA: wrist children carry their own matrix_parent_inverse, so "local (1.45,0,1.5)" does NOT
   mean 1.45 m from the wrist. Place new wrist attachments with
   matrix_world = gripper.matrix_world @ Translation(offset) after parenting.
4. chute: bottom extended x 1.20->3.40 (was 3.00), thicker (0.125), side walls raised to 0.245
   (was 0.15), 2 mounting ribs under the body end.
5. machine details merged into one object `Machine_Detail` (parent Machine_Root): window frame
   4 bars, 4 foot pads (cylinders), 3 light bezels, hopper rim torus (major 0.45 / minor 0.028).
6. product exit rebuilt: slow creep 3.0 -> 3.8 -> 4.4 and the 308->326.5 shrink are GONE.
   Now: hold x=3.0 at f280, accelerate x = 3.0 + 4.2*t^2 over f280-300 -> x=7.2, then scale to
   0.001 at f302. Verified: fully out of frame by f299 (frame right edge ~x=6.1 at z=1.2),
   so the vanish is never seen. End speed ~25 m/s.
   ZERO-KEY TRAP: the scale fcurves had keys only at 238 and 308, so removing the shrink made them
   deflate across the whole blast (f280 scale was 0.27). Needed an explicit 1.0 key at f300.

### verify
- faces 3,368 -> 7,242 (evaluated, modifiers applied). objects 41 -> 43.
- finger/ball contact numbers above; product bbox at f280 = x[2.5,3.5] z[0.701,1.699] (seated).
- loop f327 vs f1 unchanged (Product 1.35/0.001 at f1, 7.2/0.001 at f327).
- renders validation/audit_model_*, art1_*, art2_*, art3_*, art4_* (043 / 147 / 267 / 280).
- GLB: **must export with export_apply=True** or the bevels/auto-smooth never leave Blender
  (348 KB flat-shaded boxes instead of 520 KB). Final: 520,736 bytes, 38 nodes, 19 actions,
  Idea translation+rotation 327 samples each, Product translation+scale 326, Machine_Detail present.

### still blockout (next round)
- no panel seams, screws, vents; body is one rounded box.
- arm joints are still spheres on straight beams: no flanges, linkage, or cable.
- `Machine_Window` is a flat plate in a frame - no glass, no inner cavity.
- `Product` is still a 1 m cube (user deferred the form).
- materials: 9 flat greys, no textures; MAT_Hero_Light still does not wire Object Info.Color to
  emission, so the "brightness" light keys are still invisible.

---

## v12 hard-surface style pass (2026-10-30)

input v10_art (+unsaved) -> output hero_animation_v12_style.blend + .glb, 327f@60fps unchanged.
Per ART_DIRECTION_PLAN.md (reference-image style pass, proportions and rig untouched).

### P1 panels & bevels
- shell narrowed to x +-1.16; mint caps: full left plate, right plate split into 3 segments
  framing the outlet mouth (no boolean slots per plan), top plate z 1.96-2.00; 4 mm seams
  between shell/plates; all plates parented to Machine_Body so seams cannot breathe during
  the keyed +-7 cm wobble (f159-199).
- bottom: 10 cm plinth reveal + 4 tapered feet instead of a 4 mm bottom seam (the wobble
  would pierce a 4 mm gap; ruled in ledger).
- 16 screws (12-gon + slot) as one merged mesh; bevels unified 12/6/3 mm tiers.

### P2 window
- vertical superellipse 1.0 x 1.15 r0.18 cut via EXACT boolean (Cutter_Window, normals out —
  the v11 winding bug avoided); 3 layers: charcoal frame proud 0.06, cyan glow ring straddling
  the hole edge, glass alpha 0.08; open black cavity to y-0.50 + 2 static noise emission planes.
- Machine_Window rebuilt as the glass, reparented to Machine_Body, its hand-synced follower
  location keys stripped (identical values to Body's own); f165 mid-wobble verified aligned.
- lights 01-03 locZ fcurves offset +0.15 (bezel verts moved too) to clear the frame top.

### P3 bowl & chute
- hopper: revolved wide bowl, mouth ID 1.25 @z2.90, rolled lip, floor z2.35 seats the ball
  exactly, collar lands on the top plate; object kept, mesh swapped (wobble keys intact).
- chute: single U-channel prism x[1.2,3.4], floor top z0.705 preserved (product seating),
  capped+beveled end as the lip, 2 mount ribs; old 3-box set + rim torus + foot pads removed.

### P4 arm & claws
- 2 dark torus rings per joint sphere; seam rings on upper/forearm tubes.
- fingers rebuilt as HOOKED capsule claws (cross-section 0.022-0.028 x 0.036-0.046, quad-bend
  centerline): L=0.214, bend=0.025 solved by ternary search — closed contact d31=d43=0.25009
  (spec 0.2497), open d147=0.27014 (>= 0.267; v10 baseline 0.26955). Straight/flat claws
  cannot satisfy both numbers simultaneously (measured: straight 0.2443 closed / 0.2626 open).
  Finger objects/origins/rotation keys untouched.

### P5 palette
- four-color set in linear space: cream h40 s.10 v.86 (shell/hopper/arm tubes), mint h160
  s.42 v.62 (5 plates), amber h27 s.85 v.55 (chute/flap/claws/Idea emission), charcoal h240
  s.06 v.18 (base/feet/screws/rings/seams/dark hardware); MAT_Hero_Mid split+removed.
- MAT_Hero_Light rebuilt: Object Info.Color -> Emission -> Output. The object.color
  brightness keys now render (f200 strip 1.327 glows). Render-only: Object Info does not
  survive glTF; GLB lights bake at base color.

### verify (all green)
- contact 0.25009/0.25009/0.27014/0.66335 @f31/43/147/155; Idea lands (0,0,2.600) @f156.
- envelope: shell x+-1.16 z[0.10,1.90], panels to x+-1.20/top 2.00; chute x[1.16,3.4]
  floor 0.705; hopper rim 2.905; Cam_Hero 32mm (3.6,-12,4.6) untouched.
- loop f327 vs f1: Idea/Product delta 0.000000.
- poly 9,059 visible evaluated (cap 60,000; leaner than the 30-60k estimate).
- GLB 581,744 bytes, export_apply=True (baking warnings are the usual per-key-count notices).
- renders validation/style_p1..p5_*.png, each phase visually QA'd (front/side/top, window
  closeups incl. wobble frame, bowl+chute sequence, claw grab/release, four-color hero).

### known limits / next
- window noise glow breathes (strength 4.0-6.2, period 109f, 3 cycles over 327f, phase-opposed
  layers, f327==f1 within 0.002) — render-only, glTF does not carry node animation.
- end lip is a beveled cap, not a protruding roll (2.2-length iron rule).
- GLB loses the Object Info light wiring (render-only fix).
- run ledger + rulings: .superpowers/sdd/ART_DIRECTION_PLAN/progress.md

---

## v13 P0 audit pass (2026-10-31)

input hero_animation_v12_style.blend -> output hero_animation_v13_soft.blend. 327f@60fps.
Hygiene only: no geometry, no rig, no action rewrite. Plan and rulings:
docs/superpowers/specs/2026-10-31-style-v13-reference-match-design.md (commit 566f3e0).

Builder note: v12 was saved by Blender 504.3, so every step below runs on
G:\Blender\blender-5.4.0-alpha\blender.exe. Opening with 5.3.0 warns
"File written by newer Blender binary (504.3), expect loss of data".

### fixes (qa_v2/v13_p0_fix.py)
1. Q4 loop closure. Scanned every animated fcurve for evaluate(f1) != evaluate(f327):
   found 10 breaks, closed 8. All 8 were the same +0.005005 offset on location[2]:
   Arm_Mount, Machine_Body, Machine_Hopper, Machine_Light_01/02/03, Machine_LightStrip,
   Machine_OutputChute. Repair shifts the LAST key's co[1] plus both handles by the delta;
   key count and key times are untouched (23 or 26 keys, last key still at f242.65).
   These eight z-curves are one shared +-7 cm wobble offset added to each object's own base,
   so a partial fix would leave the lights and chute floating 5 mm above the body at the
   wrap: it had to be all eight or none.
   Deliberately NOT closed: Product location[0] (1.35 -> 7.20) and location[2] (0.90 -> 1.20).
   Product is hidden at f1 and scaled to 0.001 (invisible) at f327, so both endpoints are
   off-screen; rewriting them would fight the product path. Recorded in the report JSON.
2. D1 Machine_Body had ZERO material slots, so the whole shell exported as default white.
   New MAT_Body: albedo linear (0.723, 0.665, 0.578), roughness 0.45, metallic 0.
   That albedo is the reference cream read off the sheet (#DDD5C8), and it is within 0.02
   of the existing MAT_Arm — the v12 palette was never wrong, the body was simply not
   assigned anything.
3. D2 four ornament objects were parented correctly but never kept their transform, so they
   sat ~3 units away from the joint they decorate and rendered as hoops lying on the floor.
   Re-seated to the parent mesh's world bbox centre: Arm_Rings_Elbow (-0.515,-3.030,+1.769),
   Arm_Rings_Shoulder (-0.208,-0.665,+2.003), Arm_Seams_Fore (-0.537,-3.195,+1.089),
   Arm_Seams_Upper (-0.292,-1.311,+2.468); residual 0.000000 on all four.
4. D3 Cutter_Outlet, Cutter_Window, Product_Proxy_FitCheck, Product_Proxy_Large forced
   hide_render=hide_viewport=True (they had no material and were never meant to render).
   Post-check: "meshes still rendering with no material: none".

### verify
- regression vs v12 (qa_v2/v13_p0_baseline.json): actions 39, fcurves 149, keys 3,294,
  evaluated triangles 18,314, mesh objects 46 — all unchanged. Per-action key and fcurve
  counts identical. Grab contact identical to four decimals:
  f31 L 0.01799 / R 0.00614 / gap 0.31632; f147 L 0.02555 / R 0.02348 / gap 0.32185;
  f155 L 0.41537 / R 0.47581.
- loop closure, measured on renders with a PINNED camera (the auto-framing renderer moves
  the camera between frames, which makes f1 and f326 incomparable — see gotcha below):
  v12 f327 vs f1 = 7,750 px differ by >8 levels, max 132. v13-P0 f327 vs f1 = 0 px differ,
  byte-identical. The 5 mm pop is gone.
- shape metrics unchanged by P0 (qa_v2/v13_shape_metrics_v12.json vs _v13p0.json, all keys
  identical) — confirms P0 is shape-neutral.
- renders review/v13/p0_{front,right,back,top}.png, v12_* same views for comparison,
  pin_{p0,v12}_f{1,326,327}_front.png for the loop diffs.
- apples-to-apples four-view sheet review/v13/contact_v12_vs_p0.png, built by
  qa_v2/v13_contact_sheet.py from pin_v12_*/pin_p0_* rendered at frame 1 with a PINNED camera
  (--center 0.4,0,1.3 --span 5.0), so every cell shares one framing.
- the same pixels prove D1 reaches the back: back face is #99999A in v12 (neutral grey — the
  default diffuse of an unassigned shell) and #928D85 in v13-P0 (warm, R>G>B). MAT_Body covers
  the whole shell, not just the front.

### measured reference contract (reference/style_v13_ref_contract.json)
Sheet split into 3 panels at x [85,682] [776,1198] [1268,1852] = front / three-quarter / top.
Body rectangle 297 x 406 px, seeded by hand then refined to the strongest luminance gradient
within +-40 px of each edge; edge strengths 0.058 / 0.114 / 0.072 / 0.376.
Reference vs v12: body W:H 0.7315 vs 1.2889; window W/body 0.5421 vs 0.4562;
window H/body 0.6158 vs 0.6714; window H:W 1.5528 vs 1.1419; hopper dia/body 0.7778 vs 0.5905;
chute len/body 0.6768 vs 0.9655; base H/body 0.1576 vs 0.0444.

### gotchas
- Blender 4.4+ removed Action.fcurves for slotted actions. Read curves via
  action.layers[].strips[].channelbags[].fcurves or you get
  AttributeError: 'Action' object has no attribute 'fcurves'.
- In --background mode object.matrix_world is NOT refreshed after frame_set, even with
  view_layer.update(); it stays stale (often identity). Always read the evaluated depsgraph:
  obj.evaluated_get(depsgraph).matrix_world. The first version of the loop probe reported
  Product delta 0.000000 for this reason while the fcurves said 5.85.
- Auto-framed comparison renders are worthless: the framing is derived from scene bounds,
  which change with the animation. Pin --center and --span when diffing two frames.
- Machine_Chute is parented to the keyed empty Machine_OutputChute, so the chute is NOT a
  static prop and "static parts may be edited freely" does not cover it.

### known limits / next
- The P0 renders expose what P1/P2 must fix, unchanged by this pass: the body is 76% too wide
  for the reference silhouette, the window is nearly square where the reference is a 1.55
  tall ellipse, the hopper is a thin-walled open cone you can see through, Machine_Screws
  spreads 672 faces of protruding screws over the front where the reference has four flush
  bolts, and the base is 3.5x too thin. See design doc 4.3 / 5.2.
- The arm reads as a bent pipe with oversized hoops even after D2 re-seating: the rings are
  correctly positioned now but their radius is far larger than the tube they decorate (P3).
- Idea sits at (-3.55,-0.85,3.55)..(-3.05,-0.35,4.05) at f1, i.e. the orb starts parked well
  off to the upper left of the machine and flies into the claw by f31. Scripted and loop-safe,
  but it is not in the reference; a design call is owed for the hero shot.

## v13 gate: product path (2026-10-31, added before P1)

The plan's gate frames were f31/f43/f147/f155, all of which fall while `Product` is
hidden (it becomes visible at f232). Section 4.5 named this as a hole in the plan and
section 7 listed f232-f300 as the product-path gate, but no script existed. This adds
one, before P1 changes any geometry.

- Script: `qa_v2/v13_product_path_gate.py` (read-only, criteria pinned in its docstring)
- Visual evidence: `qa_v2/v13_product_path_shots.py`
- Baselines: `qa_v2/v13_product_path_v12.json`, `qa_v2/v13_product_path_v13p0.json`

Run:

```
G:\Blender\blender-5.4.0-alpha\blender.exe --background <blend> \
  --python qa_v2/v13_product_path_gate.py -- --out <json> --tag <tag>
```

Exits 3 on FAIL, so a stage cannot be accepted by accident.

### how it measures

Per frame, a 3x3 grid over the product's footprint; for each column a downward ray
finds the highest surface in a 0.080 sink band below the product's bottom (the band
keeps a sunk product measuring against the surface it sank into instead of finding
the chute's underside). `Machine_Chute`'s world bbox decides which columns still
count as "over the chute".

States: RESTING (centre supported, gap within [-0.015, +0.030]), PENETRATING
(gap < -0.015), HOVERING (centre over the chute with nothing under it), ARC
(everything over the chute is above +0.030 and z is moving), EXITED (no column
over the chute any more), COLLAPSED (scale < 0.01). FAIL on PENETRATING, HOVERING,
and FLAT_FLIGHT (constant z for 3+ consecutive EXITED frames).

The centre column is the criterion, not every column: the chute mouth is an opening,
so while the product emerges at f232-f242 its shoulder legitimately overhangs by a
few cm with the machine's side below. A first version required support under all
nine columns and failed f234/f239 on exactly that overhang; support ratio is now
reported and warned below 0.5 instead.

### verdict: FAIL, on both v12 and v13-P0

`v12` and `v13-P0` give the same verdict and differ on 2 of 96 frames (P0's -5 mm
baseline shift moved f254 and f275 across the penetration threshold by a hair).
The defect therefore pre-dates P0. Both runs, measured:

| finding | frames | numbers |
|---|---|---|
| **FLAT_FLIGHT** | f289-f300 (12 f) | product is off the chute at f289 and holds `bottom_z = 0.698` for 12 frames, `dz = 0.000`, nothing underneath, then jumps to 0.95 at f301 as it collapses |
| **PENETRATING (bounce squash)** | f255, f256 | `bottom_z` 0.695 -> 0.648, i.e. 52 mm below the chute floor top (0.705), then snaps to 0.774 at f257 (+126 mm in one frame) |
| **PENETRATING (landing dip)** | f273, f274 | -17 mm on touchdown, settling to the -5 mm rest value by f275 |

Context that the gate says is fine: the f258-f270 bounce arc peaks at +379 mm over
the chute (f263) and returns -38 mm by f270 — authored trajectory, not a defect.
Rest contact has always been a 5 mm sink (product bottom 0.700 vs chute floor 0.705);
that is the baseline, not a regression. f285-f288 still has only 6/9 and 3/9 columns
over the chute and stays RESTING because the centre of mass is still supported, which
is correct for a product sliding off a lip.

### open, needs a ruling before P1 signs off

1. `FLAT_FLIGHT` f289-f300. Either the launch is meant to be a flat shot (then raise
   `--tol-flat` / narrow the gate range and say so) or the product needs to arc down
   after leaving the lip. 12 frames at 60 fps is 0.2 s on screen; `review/v13/gate_f0294.png`
   shows it hanging in mid-air past the chute end with nothing under it.
2. Bounce squash f255/f256, 52 mm into the chute floor. If squash-into-the-floor is
   intended, raise `--tol-pen` to 0.06 and record why; otherwise the dip needs
   animation surgery, which collides with the "do not touch the animation" constraint
   and has to be decided, not drifted into.

## v13 product-path fix (2026-10-31, after both rulings: these are defects)

Rulings: the level flight is a defect; the squash that goes into the chute floor is
interpenetration, not an acceptable squash. Both live in `ProductAction.001_V2`, which
section 3.1 of the design doc froze. The freeze was written to protect working
animation from a style pass, not to make a measured defect permanent, so it is
narrowed here: `location[2]` only, additions plus two raised keys, nothing else.

Script: `qa_v2/v13_product_path_fix.py` (dry run by default, `--apply` writes).
Report: `qa_v2/v13_product_path_fix_report.json`.

### what was actually wrong

| defect | mechanism | numbers |
|---|---|---|
| squash penetration | the squash is authored (`scale[2]` = 0.400 at f253.629) but scaled **about the object centre**, so shrinking already lifts the bottom; the `location[2]` key at f255.459 then drops the centre 34 mm as well. Two moves, same direction, bottom under the floor. Correct squash-against-floor keeps the bottom planted and lets the centre RISE as the box gets shorter | f255 bottom 0.6516, f256 0.6476 vs floor 0.705 |
| level flight | `location[2]` has **no key at all after f273.756**. x was keyed every frame f280-f300; z was never keyed, so it held the landing value through the whole exit | f289-f300 bottom 0.6977 -> 0.7000, dz = 0.000, nothing underneath |
| landing dip | not a squash at all: `scale[2]` is 1.0246 (slightly stretched) and the location key eases 12 mm below the floor | f273 -10.4 mm, f274 -12.3 mm, f275 -7.5 mm |

### what the fix does

- Contact windows (f250-f258, f268-f278): where the measured bottom is below the rest
  plane 0.700, raise `location[2]` by exactly the deficit. Never lower a frame, never
  touch `scale`, so the squash still reads as a squash. 2 existing keys raised
  (f255.459 0.86 -> 0.93, f273.756 1.20 -> 1.21) and 7 frame keys inserted.
- Flight: from release at f289 (first frame fully off the lip) with v_z = 0 and
  9.81 m/s^2, key the vertical each frame to f301. 12 keys added.
- Result: `location[2]` 7 -> 26 keys, total keys 3,294 -> 3,313.
  Post-fix worst contact bottom **0.70000**, exactly the rest plane.

### scope guard (checked, not asserted)

| | before | after |
|---|---|---|
| actions | 39 | 39 |
| fcurves | 149 | 149 |
| keys | 3,294 | 3,313 (+19, all in ProductAction.001_V2 78 -> 97) |
| loop endpoint max abs delta | all 0 | all 0 |
| grab contact (finger->Idea) | 0.01799 / 0.00614 / 0.02555 / 0.02348 / 0.41537 / 0.47581 | identical |
| Product curves other than `location[2]` | - | byte-identical (dumped and diffed) |

### gate: FAIL -> PASS

`qa_v2/v13_product_path_v13p0fix.json`: counts RESTING 43 / ARC 14 / EXITED 13 /
COLLAPSED 26, zero PENETRATING, zero HOVERING, no FLAT_FLIGHT, exit=0.
Residual negative gaps are the f235-f241 emergence frames at -0.0137 (pre-existing,
inside tol_pen 0.015, untouched by this fix).

What this fix does **not** buy: the drop is physically correct but visually modest,
because only ~0.15 s of the flight is inside the frame. Droop is 4.9 cm at f294 and
8.7 cm at f297; by f300 the product is already out of frame, which is why
`review/v13/gatefix_f0300.png` is pixel-identical to the old shot while
`gatefix_f0294.png` differs by 1,251 px. A punchier read needs a launch velocity or a
different exit speed, and that is an art call, not a physics one.

### audit artifact found while verifying (fixed)

`evaluated_triangles` read 18,314 before the fix and 18,410 after, which looked like
the fix added 96 triangles. It did not. The audit inherited the frame its grab-contact
loop ended on (f155); Product is keyed to scale 0.001 there, Blender does not evaluate
its Bevel modifier, and the shell counted as a bare 12-tri cube instead of 108. Same
file measured with Product visible at f240: **18,410 both before and after**. The
audit now measures the poly budget at `POLY_FRAME = 240` and records `poly_frame` in
its JSON. 18,410 is the real number and is still well under the 25,000 budget; the
old 18,314 was an undercount and should not be quoted as a baseline.

### commits

- `gate_f0*.png` = before, `gatefix_f0*.png` = after, same camera, same frames.

## v13 P1 preflight (2026-10-31) - what P1 may not move, and the hopper ruling

Scripts: `qa_v2/v13_p1_preflight.py`, `qa_v2/v13_p1_shell_inventory.py`.
Data: `qa_v2/v13_p1_preflight.json`, `qa_v2/v13_p1_shell_inventory.json`.

### the hopper does not need shrinking. Section 12 Q1's pre-check was based on a shape this asset does not have.

Section 12 asks whether the ball "still passes the hopper mouth" after the shell narrows,
which assumes a through-hole. Measured: the hopper is a **closed shell** (0 boundary
edges), the funnel is solid below its floor, and the orb does not pass through anything -
it **rests on the pedestal top**.

Axis column at f156, straight down: orb top 2.8487 -> orb bottom 2.3513 -> **hopper 2.35**
-> hopper 2.0 -> Machine_Panel_Top 1.96 -> body 1.9. So the pedestal is a solid cylinder
(r = 0.28, z 2.0 - 2.35) and the orb (r = 0.25) sits on its top face with 1.3 mm of
clearance. Above 2.35 the funnel flares from r 0.28 to a thick rim (inner 0.62 / outer
0.68, wall 0.07) at z 2.89.

| quantity | measured | at body width 1.80 | reference |
|---|---|---|---|
| rim diameter | 1.3524 | 0.7513 of body | 0.7778 (section 4.3) - off by 3.4%, inside the doc's own +-8% |
| neck / pedestal inner r | 0.28 | - | orb needs >= 0.25 |
| orb rest | centre (0,0,2.6), bottom 2.35 | pedestal top 2.35 | - |

**Ruling: keep the hopper. Do not shrink it in P1.** Narrowing the shell to 1.80 moves
the rim to 0.751 of body width, which is the reference silhouette within tolerance. The
"0.45" figure in section 12 is a throat ratio that belongs to the reference machine, which
has a through-hole; this one has a pedestal. Comparing the two was apples to oranges, and
section 9's risk "ball jams after the mouth is narrowed" is void because no mouth is being
narrowed.

Frozen by this measurement for all later stages: **hopper pedestal top face stays at
z = 2.35**, and the funnel's inner radius at that height stays >= 0.25.

The orb occupies the hopper axis for 189 frames of 327 (first near-axis frame f117, exact
centre (0,0,2.6) at f156), so this is load-bearing, not a momentary pose.

### window: the P1 change is much smaller than the ratio suggests

Window 1.0583 x 1.2085. Ratio to body width is 0.4562 now, but 1.80 shell width already
brings it to 0.5879; the 0.64 target needs 1.1520, i.e. **+8.9% width**, not the ~40% the
raw 0.456 -> 0.64 leap suggests. P2 still owns the real rebuild (vertical superellipse);
P1 only has to stop the window from looking cramped on the narrower body.

### shell inventory (what detaches when both x faces move in by 0.26)

`Machine_Body`: 448 verts, local +-1.16 x +-0.80 x +-0.90, world z 0.1 - 1.9. Its shape is
produced by **two Boolean cutters** (`OutletCut`, `WindowCut`) plus `EdgeBevel` and a
`Smooth by Angle` nodes modifier, so a naive X scale of the body is not safe: the cutters
live in world space and would cut the wrong place.

Mounted parts that touch a moving face: left 8, right 10, top 10, front 17, back 5,
bottom 7 (overlapping sets). The ones that matter at the seam:

- arm reaches 0.704 past the left face (to x = -1.864); narrowing leaves a **0.26 gap**
  the shoulder bay has to bridge
- `Machine_Chute` starts at exactly x = 1.16, i.e. **zero overlap** with the body - the
  chute seat has no margin to hide behind, it has to span the full 0.26
- side panels (`Machine_Panel_L`, `Machine_Panel_R_SideF/SideB`), `Machine_Screws`,
  `Machine_Detail`, the window assembly (frame / glow / cavity) all sit on faces that move

### P1a plan (next): shell 2.32 -> 1.80

Working on a scratch copy, gates at each step, deliverable untouched until it passes:

1. rebuild the shell profile (superellipse section + big corner radii) in place of the
   box, keeping the two boolean cut volumes re-targeted to the new face planes
2. three junction pieces: shoulder bay (x -0.90..-1.16 at the arm's section), chute seat
   (x 0.90..1.16, full mouth height), hopper seat (body top 1.9 -> pedestal 2.0, which is
   currently a 0.1 gap in the existing asset)
3. re-seat the face-mounted parts onto the new planes; verify with this inventory diffed
   before/after - a part that stops touching is a part that fell off
4. then palette (section 5.1), then window width (+8.9%)

Gate for P1: four-view against the reference, palette sampling, `arm_root_min_x` and
`chute_mouth_min_x` unchanged, hopper pedestal top still 2.35, product-path gate still
PASS, and animation integrity (39 actions / 149 fcurves / loop deltas 0).

## v13 P1a shell rebuild, pass 1-2 (2026-10-31)

Script: `qa_v2/v13_p1a_shell.py`. Works on a scratch file, never on the deliverable:
`hero_animation_v13_p1a.blend` (regenerated from `hero_animation_v13_soft.blend` each
run, so it is reproducible and safe to throw away).

### what it does

The shell is an 8-vertex box whose silhouette comes from two EXACT booleans. Scaling it
in X would leave the cutters behind, so the base mesh is rebuilt as a rounded box
(192 verts, ring-built: rounded-rect plan outline, radius 0.20, plus a 0.10 fillet top
and bottom), the outlet cutter is translated -0.26 with the new right face, and three
junction pieces are added: `P1_ShoulderBay` (bridges the 0.26 gap to the arm mount,
which ends at x -1.18), `P1_ChuteSeat` (sleeves the outlet out to the frozen chute
mouth at x 1.16, with an opening matching the body cut), and the existing top plate
narrowed to the new width. Side panels re-seated by 0.26; base and feet meshes narrowed
0.75 in local x (their locations are animated, so the mesh is scaled, not the object).

### verified on the rebuilt scratch

| check | result |
|---|---|
| body width / height | 1.8000 / 1.8000, x +-0.9000 |
| `arm_root_min_x` | -1.864, unchanged |
| `chute_mouth_min_x` | 1.160, unchanged |
| hopper | untouched; pedestal top still the orb's rest plane, orb centre still (0,0,2.6) at f156 |
| rim / body width | 0.7513 (reference 0.7778, -3.4%) |
| window / body width | 0.5879 (target 0.64, +8.9% still to come) |
| parts still reaching outside the shell in x | 2, both legitimate: `Idea` (parked at x -3.5) and `Outlet_Flap` (belongs to the frozen chute mouth) |
| body evaluated | 704 verts / 1,404 tris |

### new gate: hard-surface intersection (`qa_v2/v13_penetration_check.py`)

The product-path gate only casts rays downward, so it could never see a box cutting
through a wall. This one builds world-space BVHs of the product and the machine per
frame and reports overlapping face pairs.

First version used `BVHTree.FromObject`, which **ignores the parent chain** - the new
junction pieces are parented to the body, so they were compared at the wrong place and
reported overlap on all 96 frames including ones where the product is scaled to 0.001.
Rebuilt from world-space polygons; the numbers below are from the fixed version.

Findings on the **untouched** asset (`v13_soft`): the product interpenetrates the chute
on **38 of 96** frames and the shell on **3**. The 38 are every frame the product is in
contact, which means the "5 mm rest sink" recorded as a baseline tolerance is a real
geometric intersection, not contact registration. The 3 shell frames are the emergence
frames f232-f240, where the product is taller (1.0) than the outlet opening (0.91).

After the rebuild: 38 frames against the chute (identical set, no regression) and **zero
against the shell** - narrowing the body removed that clip as a side effect.

One self-inflicted bug found and fixed on the way: the seat's opening cutter was built
with half-size extents, so the seat clipped the product on 7 extra frames (f281-289).
Corrected to full dimensions (`create_cube(size=1.0)` means scale == full size); those
7 frames are gone.

### open rulings

1. The 5 mm rest sink now has a name and a number: 38 frames of face overlap. By the
   standard used for the 52 mm squash (interpenetration is a defect), this is the same
   class of defect, just 10x smaller. Fixing it means moving the contact frames up
   5 mm to sit exactly on z 0.705; leaving it means writing a tolerance into the gate
   and saying so.
2. Mint composition is still wrong and is now very visible: `Machine_Panel_L`,
   `Machine_Panel_R_Top` and `SideF/SideB` are full-face slabs, and section 5.2 wants
   three narrow accents. Re-seating them flush (done) makes the slabs read as slabs.
   This is the palette/detail step, next.

### not yet done in P1

- mint accents narrowed to the reference layout; palette values to section 5.1
- window +8.9% width
- fasteners reduced (672 screw faces on the front today)
- base height: 0.0444 of body height today, reference 0.1576


## v13 P1 seat + dress (2026-10-31)

### product seating: the rest plane is not flat

Ruling: the 5 mm rest sink is interpenetration. A flat raise would have been wrong -
the chute floor moves (0.7068 at f234, 0.7137 at f239, 0.705 from f244), because the
chute inherits the +-5 mm wobble that Q4 repaired. So `qa_v2/v13_p1_seat_contact.py`
measures the surface under the product per frame and seats it at surface + 1 mm, and it
only ever raises: a frame already sitting clear of the floor is the settle read, not a
defect, and pulling it down to make the numbers tidy would flatten the animation.

Two bugs of mine, both caught by re-measuring rather than by believing the plan:

1. Applying pre-computed deltas one after another is wrong - each key insert makes
   Blender recompute the neighbouring bezier handles, so the curve the next delta was
   computed against no longer exists. Result: 15 RESTING frames became ARC and the seat
   sat 3-5 cm high. Fixed by re-measuring at every frame inside the apply loop.
2. Sampling the footprint at 1/6, 1/2, 5/6 misses the trailing edge. At f289 the centre
   is already 5 cm past the chute lip while the trailing corner is still inside the
   channel and 4 mm under the floor; that was the one frame still intersecting. Fixed
   with edge samples (0.02, 0.5, 0.98).

Result: intersection frames 38 -> 3, and all 3 are Product vs **Machine_Body** during
emergence (f236-f238), which is the pre-existing clip that the narrower P1a shell
already removes (measured: 0 on the p1a scratch). The 38 seat frames agreed exactly
with the 38 the BVH gate found - two independent methods, same answer.

### palette + mint accents (`qa_v2/v13_p1b_dress.py`)

Ruling: mint becomes one vertical band per side plus the top band, cream everywhere else.
Removed the four full-face mint plates (`Machine_Panel_L`, `_R_Top`, `_R_SideF`,
`_R_SideB`); added `P1_MintStrip_L/R` as narrow bands (y +-0.34, z 0.28..1.72,
10 mm proud) on the flat part of each side face, kept `Machine_Panel_Top` as the
section 5.2 arc band.

Albedo set from the section 5.1 p50 midtones, sRGB -> linear:

| material | target | linear set | was |
|---|---|---|---|
| MAT_Color_Mint | #8DA69D | 0.2664, 0.3813, 0.3372 | 0.1063, 0.3424, 0.2461 |
| MAT_Color_Amber | #AB642E | 0.4072, 0.1274, 0.0273 | 0.2633, 0.0698, 0.0075 |
| MAT_Arm_Dark | #424847 | 0.0545, 0.0648, 0.0630 | 0.0243, 0.0243, 0.0272 |

`MAT_Body` was already exactly the reference cream (#DDD5C8 in linear), which is why
D1 was only ever a missing assignment, not a wrong colour.

### verified after both changes

| check | deliverable | p1a scratch |
|---|---|---|
| actions / fcurves | 39 / 149 | 39 / 149 |
| keys | 3,345 | 3,345 (geometry work touched none) |
| loop endpoints | all zero | all zero |
| grab contact f31/f43/f147/f155 | identical to 5 dp | identical to 5 dp |
| evaluated triangles | 18,410 | 19,434 (budget 25,000) |
| product-path gate | PASS, negative gaps 0 | - |
| intersection gate | 3 frames, all the P1a-fixed body clip | 0 shell frames |

### still open in P1

- window +8.9% width (0.5879 -> 0.64)
- fasteners: 672 screw faces still spread over the front
- base band height 0.0444 of body height, reference 0.1576
- four-view against the reference as a contact sheet, not yet assembled
- the P1a scratch is still a scratch; the deliverable has only the animation/palette
  changes so far

## v13 P1 finished (2026-10-31) - window, base band, fasteners, and a render rig that was lying

Script: `qa_v2/v13_p1c_details.py`. Promoted to `hero_animation_v13_p1.blend`; P2
continues from there. `hero_animation_v13_soft.blend` stays as the pre-P1 state so the
stage boundary is auditable.

### what changed

- Window: x * 1.0886 applied to the cutter, frame, glow, cavity and both noise meshes in
  world space about x = 0, so the hole and the frame that sits in it move together and
  no keys or origins are touched. Measured result: **1.1520 wide = 0.6400 of body width**
  (target 0.64; was 0.5879).
- Base band: a dark band wrapping the shell's lower 0.184 m (P1_BaseBand, MAT_Arm_Dark).
  Section 4.3 asks for 0.1576 of body height; measuring the reference at native
  resolution gives about 0.10, so 0.1022 is kept and the doc's figure is flagged as
  probably measured including the feet and the contact shadow.
- Fasteners: Machine_Screws (672 faces) removed; 8 flush bolts generated, 4 front
  corners + 4 back, outside the window frame's footprint. Net -500 triangles.

### the render rig was clipping, and that invalidated every colour verdict made with it

`qa_v2/v13_p0_render.py` used Standard view transform with a bright three-point rig.
Sampling the subject pixels of the P1 front render showed **25.8% of them at #FFF-class
values** - the cream shell was blown out. Two consequences, both worth writing down:

1. "The front looks washed out" was a property of the QA rig, not of the asset. The
   material was already exactly the section 5.1 cream.
2. Any palette comparison made from those renders was measuring a clipped image.

The rig now uses AgX (with Filmic/Standard fallbacks and a --exposure argument).
After the change the clipped cluster is gone and the sampled colours land at:

| view | cluster | target | distance |
|---|---|---|---|
| right | #B0ADA8 | mint #A6BAB2 | 19.2 |
| right | #A7693C | orange #C5793E | 34.1 |
| right | #BEBAB6 | mint #A6BAB2 | 24.3 |
| front | #C9C6C2 | cream #DDD5C8 | 25.7 |

The sampler (`qa_v2/v13_p1_review.py`) removes the backdrop *before* quantising; the
first version quantised first and the backdrop gradient ate the palette slots, leaving
one usable colour out of eight. Known limit: nearest-target by RGB distance confuses
cream-in-shadow with mint, so hues within one family are not resolved.

### P1 gates, all run on the finished file

| gate | result |
|---|---|
| product-path support | PASS, 0 negative gaps |
| hard-surface intersection | **0 / 96 frames** (the narrower shell removed the pre-existing 3-frame body clip as well) |
| body width / arm root / chute mouth | 1.8000 / -1.864 / 1.160, all as frozen |
| window / rim ratios | 0.6400 / 0.7513 |
| hopper | untouched, pedestal top still the orb's rest plane |
| actions / fcurves / keys | 39 / 149 / 3,345 |
| loop endpoints | all zero |
| grab contact | identical to 5 dp |
| evaluated triangles | 18,934 (budget 25,000) |

### comparison sheet: `review/v13/p1_contact.png`

Reference panels over the matching renders. Reading it honestly, the remaining gaps are
not P1's:

- the window is a near-square rectangle where the reference is a 1.55 tall stadium, and
  it has no nebula -> **P2**
- the hopper is still a thin grey open cone where the reference is a thick-lipped cream
  bowl on a short neck -> **P3**
- the arm is a thin pipe with small hoops where the reference has a chunky arm with an
  orange cuff and a three-finger hand -> **P3**
- the chute is still the full 2.24 m brown plank; the ruling in section 4.5 wants a short
  orange scoop plus a low dark rail beyond x 2.1 -> **P3**
- body W:H is 1.00 against the reference 0.73; section 12 Q1 chose this compromise
  knowingly, and nothing in P1 changed that

## v13 P2 window + nebula (2026-10-31)

Script: `qa_v2/v13_p2_window.py`. Result: `hero_animation_v13_p2.blend` + `.glb`.

### proportions: the doc disagrees with itself, the measurement wins

Section 6 P1 asks for a window at ~0.64 of body width; section 4.3 measures the reference
at 0.5421 x 0.6158 of the body. 4.3 is the scripted measurement (the doc says it replaced
an earlier visual estimate), so the opening is built to **0.5467 x 0.6200**. P1's 0.64 is
treated as a stale bullet. The 1.5528 window aspect from 4.3 is not reproducible on this
body at all - it only holds because the reference machine is 0.73 W:H and ours is 1.00
(section 12 Q1's accepted compromise). What is matched is the window's share of the face.

### a pre-existing defect: the glass was not over the window

`Machine_Window` (the pane) had bbox z 1.298..2.102 against an opening at z 0.426..1.574,
so it covered nothing and floated above the window. It is now removed entirely: an opaque
pane was also what made the first P2 attempt render as a blank cream panel.

### three bugs of mine, each caught by measurement rather than by eye

1. Hand-built faces leave normals inconsistent. The EXACT boolean reads inside/outside from
   them, so the rebuilt cutter silently stopped cutting and the window was a solid face.
   Fixed with `remove_doubles` + `recalc_face_normals` before writing the mesh.
2. The glow ring was placed outside the opening, i.e. underneath the frame, so it was
   invisible. Moved inside: it now lines the hole's rim.
3. The cut was only 0.10 m deep, so the back of the pocket hid half the nebula. Cutter
   depth is now -0.87..-0.45 and the blobs sit inside that pocket.

### nebula: one build, not two

Section 6 asks for a volumetric render version and a mesh-based GLB version, and warns
against presenting them as identical when they are not. This ships **one** definition -
30 emissive, alpha-blended blobs - used by both, because the deliverable is the GLB and it
cannot carry volumetrics; two divergent builds would be two failure modes. The two are
identical by construction, which is a stronger guarantee than a documented difference.
The section's gate item "two differences written down" is therefore satisfied with
"there are none, and here is why".

That parity needed one real fix: a Mix(Transparent, Emission) stack renders correctly in
EEVEE but the glTF exporter does not translate it, so the first GLB came out with **no
alphaMode** - the nebula would have been opaque in every viewer while looking soft in the
render. Rebuilt on Principled (Emission Color/Strength + Alpha), which the exporter does
understand.

### P2 gates

| gate | result |
|---|---|
| render: nebula readable | yes - clustered pink/cyan plume inside a dark pocket |
| GLB: window is not a dead black box | 30 blob nodes, 3 emissive materials, alphaMode BLEND, baseAlpha 0.45-0.55 |
| GLB texture references | **images 0, textures 0, samplers 0** |
| render vs GLB divergence | none by construction (single material definition) |
| product-path gate | PASS, 0 negative gaps |
| intersection gate | 0 / 96 frames |
| actions / fcurves / keys | 39 / 149 / 3,345, loop endpoints all zero |
| triangles | 20,958 (budget 25,000) |

Comparison sheet: `review/v13/p2_contact.png`.

### what P2 deliberately did not do

- the window frame is not yet the thick charcoal band of the reference; the band is 0.072
- the machine still has a thin grey open-cone hopper and a thin pipe arm (P3)
- the chute is still the 2.24 m brown plank (P3)

## v13 P3a: grab criterion pinned, chute split, hopper rebuilt (2026-10-31)

### grab criterion, fixed before any claw change

Section 6 P3 requires the contact criterion to be executable before the claw is touched,
because the old record's numbers (0.25009 / 0.27014) cannot be reproduced by any current
method. `qa_v2/v13_grab_gate.py` pins it as finger-vertex -> Idea-vertex (the same
quantity `v13_baseline_audit.py` reports), with bands taken from the P0 baseline:

| frame | meaning | L | R | band | verdict |
|---|---|---|---|---|---|
| f31 | closed | 0.01799 | 0.00614 | 0.002..0.060 | ok |
| f43 | closed | 0.01799 | 0.00614 | 0.002..0.060 | ok |
| f147 | open | 0.02555 | 0.02348 | 0.005..0.080 | ok |
| f155 | released | 0.41537 | 0.47581 | >= 0.300 | ok |

It also counts face overlap between each finger and the orb, so a chunky pad that grips
by interpenetrating fails even if the distance number looks healthy. Passes unchanged
after the chute and hopper work, which is the point: those did not touch the claw.

### chute: support frozen, read halved

x 1.16..2.10 is now a cream scoop with an orange trough (cream outside, `MAT_Color_Amber`
on the floor's top faces only), and x 2.10..3.40 is a low narrow dark rail. The channel
floor stays at **z 0.705**, so all 38 seated contact keys remain valid - confirmed by the
product-path gate (43 RESTING, 0 negative gaps). Support length is unchanged at 3.40,
which section 4.5 froze so the product is not left in the air.

### hopper: cream bowl instead of a grey open cone

Lathe-built: solid pedestal (r 0.28, top **z 2.35**), flaring bowl to r 0.62 inner,
0.07 wall, thick rolled rim to r 0.745, in `MAT_Body` cream. The orb's rest plane is
verified by a downward axis ray: first hit is still **2.35 Machine_Hopper**, then 2.0
(pedestal bottom), 1.96 (top plate), 1.9 (body) - identical to before the rebuild.

The hopper carries its own 26 z-keys from Q4, so the mesh is built in local space about
its origin at z 2.45. Writing world coordinates into a translated object is exactly the
mistake that silently moved the window cutter in P2.

### two of my own bugs, both measured

1. A material-index sentinel of -1 was assigned straight to `face.material_index`
   ("outside usable range"). Fixed to fall back to the box's default.
2. The rebuilt chute reported **7 frames of interpenetration** while the two objects
   measured **0.306 apart** at f236 with zero vertices inside each other's bbox. Cause:
   the three boxes were welded with `remove_doubles` at their coplanar seams, and the
   existing `Bevel_Art` modifier then built self-intersecting geometry on the
   zero-thickness joint, which makes any overlap test on that object lie. Fixed by not
   welding the boxes and starting the walls 5 mm inside the floor. Penetration went to
   **0 / 96**.
   Note for later: triangulating the BVH made the tool worse, not better - a known-clean
   file went from 0 to 27 flagged frames - so the gate was reverted and the geometry was
   fixed instead of the instrument.

### P3a gates

| gate | result |
|---|---|
| grab | PASS, all four frames in band, zero finger/orb face overlap |
| product path | PASS, 43 RESTING, 0 negative gaps |
| intersection | 0 / 96 |
| actions / fcurves / keys | 39 / 149 / 3,345 |
| triangles | 20,646 (budget 25,000) |

### still open

- **claw**: still a thin pipe with oversized hoops; needs the rounded pad rebuild plus the
  fixed third finger. The criterion is now pinned, so this can be judged.
- the hopper's neck is a straight cylinder; the reference has a short cream neck with the
  mint collar under it
- GLB has not been re-exported since P2

## v13 P3b (2026-11-01) - the hand rebuilt as a three-finger claw, and a NaN that was mine

Stage file: `hero_animation_v13_p3b.blend`, exported as `hero_animation_v13_p3b.glb`
(1,094,460 B). P3a's `hero_animation_v13_p3.glb` is untouched.

### what the reference actually shows, at full resolution

Cropped from `reference/style_v13_ref.png` into `review/v13/ref_front_claw.png` and
`review/v13/ref_iso_full.png`: cream forearm, a **dark narrow wrist cuff carrying a thin
orange clamp**, a dark irregular palm block, then **three chunky orange fingers spread
120 degrees** (up, lower-left, lower-right) around a small orange orb. Every finger is
visibly jointed, thick at the base, rounded at the tip, slightly hooked. The orb *is* the
grabbed `Idea`, so the amber-on-amber colour scheme the asset already had was correct; what
was wrong was the shape, not the colour.

### the geometric deadlock, stated before modelling

At f31 the orb is `r 0.25` with its centre **0.396** ahead of the wrist. The old palm block
was 0.337 wide, so the orb was *wider than the palm*. Sweeping forward on the y=0 plane,
the orb surface is reached at **x = 0.146** - barely past the wrist. A cage of fingers
closing *around* the orb, the way the reference reads, is therefore not reachable: the
fingers would have to arc out past x = 0.579 to meet in front of it. The ceiling is
**three pads touching the orb with the palm cupped behind it**, and that is what P3b
delivers. Changing it would mean changing the orb radius, which the animation pins.

### geometry as built (all in wrist space, then transformed into each object's own space)

| part | construction | tris |
|---|---|---|
| `Arm_Gripper` (palm) | UV sphere 32x18 scaled to RX 0.076 / RY 0.156 / RZ 0.134, centred CX 0.058, front edge tapered `f = 1 - 0.10k^2` | 1,088 |
| `Arm_WristCollar` | cone ring x -0.118..0.006, radius 0.090 -> 0.101 on an S curve, 24x12, both ends fan-capped | 312 |
| `Arm_Finger_L/R` | 4-point cubic Bezier, radius `prof(t) = (0.0455 + 0.0030 sin(pi min(t/0.60,1))) * (1 + 0.13e^-((t-0.30)/0.10)^2 - 0.10e^-((t-0.50)/0.055)^2 - 0.09e^-((t-0.78)/0.05)^2)`, `NSEG 28`, `NRING 16`, width 0.95, thickness 1.08 | 1,024 each |
| `Arm_Finger_C` | new object, parent `Arm_Wrist`, `matrix_parent_inverse` and `matrix_basis` both identity, no action, `MAT_Color_Amber`; Bezier P0 (0.050,0,-0.060) P1 (0.115,0,-0.150) P2 (0.170,0,-0.255) P3 (0.230,0,-0.300), radius `0.0505 + 0.0030 sin(pi t)`, thickness 1.02 | 1,024 |

`Arm_Seams_Fore` and `Arm_Seams_Upper` (the floating thin lines) are deleted.

Left finger control points, the ones that finally worked:
`P0 (0.090, 0.145, 0)`, `P1 (0.160, 0.1962, 0)`, `P2 (0.300, 0.380, 0.095)`,
`P3 (0.3737, 0.2542, 0.1783)`; the right finger is the exact mirror
`(x, -y, z)`. The radius formula's three Gaussians are the knuckle grooves - a raised
band at t 0.30 and pinches at 0.50 and 0.78.

### five failed attempts, all measured

1. **Flat oval cross-section.** Semi-axes 0.048 x 0.036 rendered as "one fat finger and one
   thin twig", because the review camera looks mostly down world Y and the finger's narrow
   axis pointed at it.
2. **Raising the tips.** P2 to z 0.028 and P3 to z 0.072 changed almost nothing visually -
   the two fingers are mirror-symmetric in y, so from that camera one is always hidden
   behind the orb.
3. **Wrapping the tips toward the orb's front.** `P3 = (0.375, 0.240, 0.168)` drove
   `overlap_faces` to 60/36 and the distances to 0.00283/0.00372, straight to FAIL. Sweeping
   P3 outward along the orb normal (k 0.2946 -> 0.322) only moved the worst clearance from
   -0.00868 to -0.00513, because **the worst point sits at t ~ 0.5, not at the tip**.
4. **The third finger's cross-section axis.** `S_AXc = (0.636, 0, -0.772)` against a tangent
   of `(0.733, 0, -0.678)` gives a dot product of **0.989** - nearly parallel, so the
   section collapsed to a line 0.0371 wide and rendered as a thin stick. Fixed by deriving
   the frame from the tangent (`u` = Y projected onto the tangent's normal plane,
   `v = t x u`) which produced 0.1142 x 0.1026 x 0.2845.
5. **The palm buried in the orb.** The first palm block reached x 0.185 while the orb
   surface sits at x 0.1462 on y=0, so 0.039 of palm was inside the orb and rendered as a
   grey wedge cutting through it. The grab gate only tests finger-vs-orb, so it could not
   see this. Replaced by the ellipsoid above: `palm_dist_to_orb = 0.01466`.

The winning move for the fingers was **bulging P2 outward** rather than reaching with P3:
scanning `worst(P2,P3) = min_t(|cb(t) - C| - 0.25 - prof(t))` over the feasible region gives
a best surface clearance of **0.0143**, and the shape reads as a hooked claw instead of a
straight tube.

### the NaN: a degenerate face I built, amplified by a modifier

`export_apply=True` died with
`ValueError: cannot convert float NaN to integer` at `io_scene_gltf2/blender/exp/export.py:515`
(`if int(obj) == obj:`). `export_apply=False` exported fine, which localised the fault to
"applying modifiers", not to the scene. F-curves, object transforms, material inputs and raw
mesh data were all clean.

Evaluating every mesh through the depsgraph and counting non-finite vertices found exactly
two offenders: `Arm_Finger_L` and `Arm_Finger_R`, **15 NaN vertices each**. Their raw meshes
held **16 zero-area faces and 16 duplicate vertices** - the tip cap emitted a ring whose
radius had already collapsed to zero, so it produced degenerate quads; `Bevel_Art`
(width 0.006, segments 2) then turned those into NaN.

Fix: `bmesh.ops.remove_doubles(dist=1e-5)` + `bmesh.ops.dissolve_degenerate(dist=1e-6)`,
then drop any face still under 1e-10 area and any vertex left without faces. Both fingers
settled at **498 verts / 512 polys**, min face area 1.047e-4, and evaluated to
578 verts / 592 polys with **zero NaN**. The grab gate values did not move at all - cleaning
degenerate geometry changes nothing you can grip with.

### P3b gates

| gate | result |
|---|---|
| grab (`v13_grab_gate.py`, pinned, untouched) | **PASS** - f31/f43 L 0.01148 R 0.01432, f147 L 0.01808 R 0.02085, f155 L 0.40630 R 0.45380, overlap 0 everywhere |
| loop closure | f1 vs f327 on 97 objects' `matrix_world`: **zero difference**; rendered pixels: **0 px above 8 levels** |
| finger vs machine intersection | **0 hits / 1,640 pairs** (4 claw objects x 5 machine parts, 82 frames at step 4) |
| actions / fcurves / keys | 37 / 147 / 3,331 |
| evaluated triangles | 22,650 (budget 25,000) |
| GLB | 76 meshes, 83 nodes, 15 materials, 18 animations, 21,802 tris, **images 0 / textures 0 / samplers 0**, no non-finite accessor bounds |

`tip_gap_LR` dropped from 0.31632 to 0.22482 (f31) and 0.20923 (f147) because the fingers are
now thick hooks. That number is reported, not constrained.

### the action count changed, and it is not a regression

Frozen invariants said 39 actions / 149 fcurves / 3,345 keys; this file has 37 / 147 / 3,331.
The two missing actions are `MAT_Window_Noise1Action` and `MAT_Window_Noise2Action` - the
window-noise material drivers. P2 rebuilt the window and deleted the nodes they animated, so
they became zero-user datablocks and were dropped on the first save-reload cycle. They are
never evaluated (no object references them) and the window noise never survived glTF anyway.
The 37 that remain include the 18 that actually drive the rig.

### animation QA sheet

`review/v13/p3b_anim_contact_sheet.png` - 22 frames (every 16th across 1..327, plus 327) in a
5x5 grid at 420 px cells, rendered from a temporary `QA_AnimCam` (lens 50) framing the whole
act: centre (-0.075, -0.588, 1.982), radius 4.284, distance 12.138. The camera and its drive
are removed before saving, so the deliverable never contains QA furniture.

Reading it: orb starts far upper-left, arm swings in and takes it (f17-f49), holds through
the middle (f65-f145), lifts and releases over the hopper (f161-f241), product emerges and
rides the chute (f257-f289), then the loop returns to f1. Frame-to-frame mean absolute
difference peaks at **3.807 / 255** (f273 -> f289) and never pops; f1 and f327 are
pixel-identical.

### export truth - checked two ways, because the first one lied

`review/v13/p3b_glb_roundtrip_f31.png` re-imports the GLB into a scratch scene and renders
the hand: the claw survives the round trip as three hooked orange fingers on an ellipsoid
palm. But in that render the orb sits far up-left instead of in the claw, and that is **not a
GLB defect** - Blender's glTF importer turns each of the 18 clips into a separate action and
activates only one per object, so the frame-31 pose is assembled from whatever happened to be
live. Do not read animation state out of a Blender round-trip render.

The numeric check settles it. Parsing the GLB's own accessors, `IdeaAction_V2` carries
**327 keys over t 0.0167..5.45 s**, and its first and last samples are identical
`(-3.3, 3.8, 0.6)` in glTF Y-up, which is Blender `(-3.3, -0.6, 3.8)` - exactly f1, so loop
closure survives the export. At t 0.5 s the sampler reads `(-3.2922, 1.7098, 0.623)`, i.e.
Blender `(-3.2922, 0.623, -1.7098)`, against the blend's f30/f31 values around
`(-3.2949, -0.6181, 1.7219)` - the same pose, one frame apart in the sampling.

### how P3b was authored - and the gap that leaves

Everything above was applied live through the Blender MCP bridge on port 9876, per the
project rule that this stage runs through MCP only. **There is no standalone
`qa_v2/v13_p3b_claw.py`.** The parameters in this section are the source of truth, and the
next stage script should consume them; until that script exists, P3b cannot be replayed from
the P3a asset the way P1/P2/P3a can.

## v13 P3c (2026-11-01) - reference pass 2: arm chain, window slimming, body roundness

A second, much closer read of `review/v13/ref_iso_full.png` overturned three earlier readings
and drove this pass. All of it was applied live through the Blender MCP bridge on port 9876.

### what the reference actually shows (corrections)

1. **The arm is a ball-and-tube chain, not a bent pipe with big rings.** Cream ball socket on
   a cream boss that sits on the mint side panel, with a **thin dark ring at each joint**;
   cream upper arm -> cream elbow ball -> cream forearm -> **dark wrist sleeve + thin amber
   ferrule** -> three **flat leaf-shaped** amber fingers around the orb. Dark metal appears
   only at joint seams and the wrist sleeve.
2. **The hopper is a wide funnel with a short thick neck and a thick rolled lip**, sitting on
   a mint rounded-rectangle recessed pad on the top face - not a mint band around the machine.
3. **The plinth is a dark rounded band with four small round feet**, and the front panel
   carries one amber and one mint button, each on a thin dark collar.

### what was changed

| item | change |
|---|---|
| `Arm_Rings_Shoulder`, `Arm_Rings_Elbow` | **deleted** - not in the reference at all |
| `Arm_UpperArm`, `Arm_Forearm` | rebuilt as true surface-of-revolution tubes: shoulder `(-1.5,0,1.5)` -> elbow `(-1.6678,-1.2914,2.4297)` L 1.6 r 0.108->0.098; elbow -> wrist `(-1.7108,-1.6224,1.07)` L 1.4 r 0.105->0.082. Object scale reset to (1,1,1), size baked into the mesh, `Bevel_Art` **removed** (dense curved surface + bevel is the same NaN trap that killed the fingercaps), `Smooth by Angle` kept. 700 v / 674 f and 588 v / 562 f |
| joint seam rings | built into the tube mesh as a proud ring (+0.013 r, ±0.011 wide), second material slot `MAT_Arm_Dark`, placed at `t = sqrt(r_ball^2 - r_tube^2)/L` -> 0.090 shoulder, 0.929 / 0.0765 at the elbow |
| `Arm_Shoulder_Joint`, `Arm_Elbow_Joint`, `Arm_Base` | material `MAT_Arm_Dark` -> **`MAT_Arm`** (the reference's joints are cream; only the seam rings are dark) |
| window | `Machine_WindowFrame` was 1.128 x 1.26 (aspect 1.117, read as a round window). Frame + Glow + Cavity + 30 `P2_Nebula_*` + `Cutter_Window` scaled in X by **K=0.78** about each part's own X centre -> frame 0.8798 x 1.26 = **aspect 1.4321** |
| `Machine_Detail` | the three Ø0.196 grey discs on the front (x -0.3 / 0 / +0.3 at z 1.75) were three connected islands inside this object. Removed by bmesh connected-component selection (`cz > 1.5`); 12 f / 16 v left (the two side boxes) |
| `Machine_Body` | `EdgeBevel` 0.012/3 -> **0.05/4**, and the modifier order changed from `OutletCut -> WindowCut -> EdgeBevel -> Smooth` to **`EdgeBevel -> OutletCut -> WindowCut -> Smooth`** so the cut edges are not re-beveled into the window frame |
| `Machine_Panel_Top` | was a floating x ±0.94 / y ±0.8 board at z 1.96..2.0 with a 0.06 air gap above a 1.9 body top. Rebuilt inset: x ±0.80, y ±0.70, **z 1.885..1.925** |
| `Machine_Hopper` | rebuilt as a lathed vessel: neck r 0.285 -> flare -> thick rolled lip (outer 0.678, inner 0.503, so a 0.167 lip), inner wall returns to r 0.250. World **r 0.678, z 1.925..2.674**, 1,776 tris. Only mesh vertices were touched - the object carries `Machine_HopperAction_V2` (26 z keys) and its location must not move |
| `Machine_Base` | its 16 top vertices sat at z 0.0 while `Machine_Body`'s underside is at 0.1, i.e. the body floated 0.1 above the plinth. Raised to **z 0.12** (above the body underside, avoiding coplanar z-fighting) |
| `P3c_Button_Power`, `P3c_Button_Mode` | new, no action. Lathed about Y, front slightly domed, r 0.042 amber at (x 0.075, z 0.333) and r 0.027 mint at (x 0.215, z 0.333), protruding 0.048 to y -0.848. Parented to `Machine_Body` with `matrix_parent_inverse = body.matrix_world.inverted()`, `matrix_basis` identity |
| `Machine_Light_01/02/03` | were Ø0.14 spheres bulging 0.09 out of the front panel - three big pale discs in every front view and not in the reference. Scaled to 0.26 (Ø0.0218) and sunk so they protrude **0.004** (y -0.804..-0.664); their z-jitter action is untouched |

### gates after this pass

`qa_v2/v13_grab_gate.py` -> **PASS**, and byte-identical to P3b: f31/f43 L 0.01148 R 0.01432,
f147 L 0.01808 R 0.02085, f155 L 0.40630 R 0.45380, overlap 0 everywhere, tip_gap_LR
0.22482 / 0.22482 / 0.20923 / 0.20923. The hand was not touched, so this is the control that
the machine edits did not disturb the grip.
`qa_v2/v13_product_path_gate.py` -> **PASS**, counts RESTING 43 / ARC 14 / EXITED 13 /
COLLAPSED 26, arc 257..270 peaking +0.379 at f263, first_exited f289, negative gaps 0.
Loop closure: every one of the 93 objects' `matrix_world` compared at f1 vs f327 -> **zero
difference**. Actions 37, fcurves 147, keys 3,331 - all equal to the frozen P3b values.
Budget: **23,854 / 25,000** triangles.

### gotchas added by this pass

- `o.location += dloc` **and** moving vertices moves the part twice. The three front lights
  first flew out to y -2.448 this way. Move the object OR the geometry, never both.
- Converting world coordinates into a mesh needs `obj.matrix_world.inverted()`. Writing world
  z straight into a hopper whose object sits at z 2.45 put it at z 4.4..5.1.
- `evaluated_depsgraph_get()` must be re-fetched after a geometry edit; a stale depsgraph
  reports the pre-edit bounding box and makes the edit look like a no-op.
- `sc.evee` is not a thing; it is `sc.eevee`.
- An exception mid-script leaves the temporary `QA_*` camera and lights in the scene. Clear
  them before re-running or the next "clean" render carries stale rigs.

### still open after P3c (honest list)

1. **The chute is 2.24 long = 1.24 of body width; the reference measures 0.677.** It cannot
   be shortened without dropping the product: `ProductAction.001_V2` carries the product from
   x 1.36 to 5.9 along that surface over f232..f289, and the part is parented to the keyframed
   empty `Machine_OutputChute`. From behind, the chute reads as a slab plus a thin rail with
   no visible support. This is the single largest remaining silhouette difference.
2. `Outlet_Flap` reads as a detached flat plate at the chute mouth in the f1 pose; it is
   animated, so its rest pose cannot be re-authored casually.
3. The window interior is still light grey behind the pale nebula spheres; the reference is a
   dark teal cavity with a diffuse nebula. That is a material change, deliberately deferred.
4. No four small round feet yet, and the mint side panel is a thin strip rather than the
   reference's large rounded panel.
5. `Cam_Hero` plus two suns only is not the reference's studio look. The shape reads much
   better under the `QA_*` rig than under the shipped camera.

## v13 P3e (2026-11-02)

Reference-fidelity pass on the outlet side plus the base plinth. File
`hero_animation_v13_p3e.blend`. 98 objects, 88 meshes, 37 actions, 23,322 / 25,000 triangles,
loop broken 0, NaN 0, texture nodes 0. No action, object origin or parenting was changed.

### What changed

1. **`Machine_Chute` dark rail narrowed.** Side walls y ±0.52 → ±0.42 (tip ±0.36); the
   underside at the tip lifted 0.605 → 0.672 so it tapers instead of ending as a plank edge.
   The support surface (`z = 0.705`, x 2.1…3.4) is untouched, so the product path is
   bit-identical. A first attempt at ±0.34 made the gate emit a low-support warning
   (ratio 0.33 over f248…f288); ±0.42 restores ratio 1.0 for the frames that had it.
2. **`P1_ChuteSeat` rebuilt.** It was a 1.07-tall portal frame (the "ear" in every 3/4 and
   back view). Now a 0.55-tall collar: x 0.90…1.16, outer y ±0.745 / z 0.455…1.005, inner
   opening y ±0.685 / z 0.505…0.955 so it hugs the scoop cross-section instead of
   intersecting it. Rebuilt as a four-wall tube with rounded corners (radius 0.035) plus a
   0.008 chamfer; 380 → 364 tris. Rebuilding beat scaling: scaling z squashed the opening and
   pushed the frame through the scoop.
3. **`Outlet_Flap` re-authored as a flush hatch.** Object scale (0.04, 0.8, 0.5) baked to
   (1, 1, 1); the eight vertices were rewritten so that in the rest pose (−30° about Y) the
   panel sits flush on the body's right face: x 0.896…0.936, y ±0.62, z 1.012…1.44. Material
   `MAT_Color_Amber` → `MAT_Body`. Origin, parent and the single `rotation_euler[1]` fcurve
   are untouched, so it still swings out over f227…f255.
4. **`Machine_Base` overhang trimmed.** Right edge x 1.158 → 0.925 so the plinth no longer
   pokes out under the scoop; footprint now x ±0.925, y ±0.8, z 0…0.12, bevel 0.018 / 2.
   With `P1_BaseBand` (z 0.1…0.284, bevel 0.020 / 2) the plinth now reads as one charcoal
   block 0…0.284 = 0.158 of body height against the reference's 0.1576.
5. **`Machine_Panel_Top` bevel 0.012 / 2** so the top plate stops reading as a hard seam.
6. **Four light meshes hidden.** `Machine_Light_01/02/03` (three pale discs at z 1.75) and
   `Machine_LightStrip` (the front strip that sliced the charcoal band in half) do not exist
   in the reference. They are hidden, not deleted: data and their `*Action_V2` curves are
   kept for a later FX pass. **The GLB exporter must use `use_visible=True`, otherwise they
   come back.**

### Preflight finding (recorded because it constrains every later chute change)

A downward raycast from the product's bounding-box centre onto `Machine_Chute`'s evaluated
mesh, over all 57 RESTING+ARC frames, hits the cream shell (`MAT_Body`) **0 times**. The
product rides the amber inner floor (`MAT_Color_Amber`) until its centre reaches xc 2.09 and
the dark rail (`MAT_Arm_Dark`) from xc 2.22 out to xc 3.38; at f287…f288 only the rear edge
rests on the rail's tip. Cutting the cream shell would therefore have been safe, but the
shell already ends at x 2.1, and the rail cannot be shortened without failing the path gate.

### Gate evidence

- `qa_v2/v13_grab_p3e.json` — **PASS**, bit-identical to P3b/P3c/P3d (f31/f43 L 0.01148
  R 0.01432; f147 L 0.01808 R 0.02085; f155 L 0.40630 R 0.45380; overlap 0 everywhere).
- `qa_v2/v13_product_path_p3e.json` — **PASS**, RESTING 43 / ARC 14 / EXITED 13 /
  COLLAPSED 26, arc peak +0.379 @f263, first_exited f289, negative gaps 0.
- `qa_v2/v13_shape_metrics_p3e.json` — charcoal_h_to_body_h 0.1578 vs the reference's 0.1576;
  chute_len_to_body_w still 1.2444 because the metric measures the whole object, which
  includes the structural tongue. The cream scoop alone is 0.94 long (0.52 of body width)
  and the seat-to-scoop-end span 0.90…2.10 is 1.20 (0.667), against the reference's 0.677.
- Loop closure: 98 objects, `matrix_world` f1 vs f327, 0 broken.
- Renders: `review/v13/p3d5_front.png`, `p3d5_hero_3q.png`, `p3d5_base.png`,
  `p3d3_outlet_closeup.png`, `p3d4_right.png`.

### Still open

1. The scoop still reads as a tray with an orange floor plus a dark tongue; the reference is
   a small rounded spout. The tongue is structural (see preflight), so this stays.
2. The three-finger claw is still round tubes; the reference is flat, wide leaves. That is
   batch 3 and it needs the grab gate re-run.
3. Window cavity, window frame and the mint glow are still flat colour blocks — material pass.
4. `Product` is `hide_render = True` in the shipped file (pre-existing, not a P3e change).
5. The top mint surface is a plain plate; the reference wraps a mint band over the top and
   down the right shoulder. *(fixed in P3f — see below)*

## v13 P3f (2026-11-02)

User rulings that drove this pass (verbatim, one per item): hide the three gray lights and the
front-bottom light strip (keep the data, do not delete); rework the top mint into a band that
wraps over the top and down to the shoulders; widen the front window; enter batch ③ but **keep
the fingers as round tubes** because they read better than flat leaves.

The fourth pending item, the base band, turned out to be a measurement error rather than a
conflict: the charcoal region is `Machine_Base` (z 0…0.12) plus `P1_BaseBand` (z 0.1…0.284),
which butt together, so its total height is 0.284 = **0.1578** of body height against the
reference's 0.1576. The earlier 0.102 figure only measured `P1_BaseBand`. No band enlargement
and no button relocation were needed, and the A/B/C options were dropped.

### Changes

1. **Top mint skin** — deleted the flat plate `Machine_Panel_Top` (a separate 0.04-thick slab
   sitting 0.025 proud of the body top; from the side it read as a pane of glass laid on the
   box). `P3f_TopSkin` is instead built from `Machine_Body`'s *evaluated* mesh: take the faces
   with `center.z >= 1.715 and normal.z > 0.22 and abs(normal.y) < 0.52` (top face plus the
   left/right shoulder bevels, front and back faces excluded), offset every vertex 0.0025
   along its normal, and rebuild as a separate object (214 tris, 128 verts, world
   z 1.8342…1.9024, x ±0.8966, y ±0.7555), `MAT_Color_Mint`, all faces smooth, parented to
   `Machine_Body` with `matrix_parent_inverse = body.matrix_world.inverted()`. A conformal
   skin reads as paint; a bevelled cover plate of any thickness reads as a glass table top.
2. **Side mint connection** — `P1_MintStrip_L` widened from y ±0.34 to **±0.60**
   (`scale.y = 1.24/0.68 = 1.8235`) and both L/R strips raised so their top edge meets the
   skin at **z 1.845** (`scale.z = (1.845-0.28)/1.44 = 1.0868`, `location.z = (0.28+1.845)/2
   = 1.0625`). The right strip was *not* widened in y: `P1_ChuteSeat` occupies z 0.455…1.005
   there and the two would interpenetrate.
3. **`Arm_Mount` material** `MAT_Arm_Dark` → `MAT_Arm`. It is a dark box spanning
   x −1.928…−1.18, z 0.7…1.0 that does not exist in the reference; the reference has a cream
   raised shoulder pad there. Material only, no transform, no action touched.
4. **Window widened in x** — two factors, F1 = 1.1091 then F2 = 1.14625, multiplied into the
   `scale.x` of `Machine_WindowFrame`, `Machine_WindowGlow`, `Machine_WindowCavity` and
   `Cutter_Window`, with the 30 `P2_Nebula_*` `location.x` scaled by the same factors (their
   radii were left alone). Result: frame x ±0.5593, glass x ±0.4879 → **0.9757 = 0.5421 of
   body width, an exact match to the reference**. Cavity 0.9599, cutter 0.9757.
5. **Window heightened in z** — about the common centre `KC = 1.0128`, `scale.z *= KZ =
   1.1341` and `location.z = (loc.z - KC) * KZ + KC + DZ` with `DZ = 0.1019`, applied to the
   same four objects plus the nebulae's z. Final frame z **0.3985…1.828** (0.0235 clear of the
   button tops at 0.375, 0.0215 clear of the top bevel start at 1.85), glass z 0.4802…1.7458
   (height 1.2656), cutter z 0.4674…1.733. This is the ceiling: taller runs into the button
   row, wider runs into the body's own width.
6. **Fingers thickened (batch ③, tubes kept)** — per-vertex PCA on `Arm_Finger_L/R/C`: take the
   world-space point cloud, SVD for the principal axis `a`, split each vertex into an axial
   component `t` and a perpendicular component `q`, then scale `q *= 1.12` while leaving `t`
   alone. That thickens the whole bend evenly and does not move the endpoints.
   `Arm_Finger_L/R` axis (0.3906, −0.7328, −0.5572) / (−0.5649, −0.6086, −0.5572), axial length
   0.4227, perpendicular radius 0.08828 → 0.09887; `Arm_Finger_C` axis
   (−0.0805, −0.6198, 0.7806), length 0.3505, radius 0.06174 → 0.06915. A first attempt at
   1.16 dropped the f31 left-finger clearance to 0.00381 against a 0.002 floor — 0.0018 of
   margin — so it was backed off to 1.12.

### The window metric has a unit trap

`v13_shape_metrics.py` `window_w_to_body_w` measures **`Machine_WindowGlow`** (glass plus the
mint ring), not the `Machine_WindowFrame` outer box. Scaling the frame to 0.5421 still reported
0.4729 and cost a wasted iteration. Note also that the reference's three window numbers cannot
all hold at once: 0.5421 × 1.5528 = 0.8416, but `window_h_to_body_h` is 0.6158. One of the
three must give.

### Gate evidence

- `qa_v2/v13_grab_p3f.json` — **PASS**. f31 L 0.00557 R 0.01118; f147 L 0.01267 R 0.01492;
  f155 L 0.40271 R 0.45016; overlap 0 everywhere. Tighter than P3e because the fingers are
  thicker, but still clear of the 0.002 floor.
- `qa_v2/v13_product_path_p3f.json` — **PASS**, RESTING 43 / ARC 14 / EXITED 13 / COLLAPSED 26,
  arc peak +0.379 @f263, first_exited f289, negative gaps 0, support ratio 1.0 on every frame
  (9 / 6 / 3 columns over the chute).
- `qa_v2/v13_shape_metrics_p3f.json` — `window_w_to_body_w` **0.5421** (reference 0.5421),
  `window_h_to_body_h` **0.7032** (reference 0.6158), `window_h_to_w` **1.2972** (reference
  1.5528, unreachable — see the unit trap above; the geometric ceiling is about 1.33),
  `charcoal_h_to_body_h` 0.1578 (reference 0.1576), `hopper_dia_to_body_w` 0.7533,
  `chute_len_to_body_w` 1.2444, `window_centre_dz_to_body_h` 0.0628,
  `claw_reach_beyond_body_w` 0.4411, `base_h_to_body_h` 0.0667, `body_w_to_h` 1.0.
- Loop closure: 105 objects (98 plus the 7 temporary QA rig), `matrix_world` f1 vs f327, worst
  delta 0.0, 0 broken. NaN objects 0, texture nodes 0, 16 materials, 37 actions, 147 fcurves,
  3,331 keys, **23,540 triangles of 25,000**.
- Render rig: `QAKEY` area light at (−4.5, −6.5, 7.5) 320 W size 6, `QAFILL` (5.5, −4.5, 3.0)
  110 W size 7, `QARIM` (0.5, 6.5, 5.0) 170 W size 6; cameras `QACAM` front at (−0.05, −9, 1.0)
  lens 80, `QACAM_3Q` (−5.2, −6.4, 4.6) lens 68 aimed at (−0.05, 0, 1.0), `QACAM_TOP`
  (−2.6, −4.2, 6.4) lens 62 aimed at (−0.05, 0, 1.55), `QACAM_CLAW` (−3.15, −3.55, 1.80)
  lens 85 aimed at the claw centre (−1.4917, −1.7935, 0.8692). EEVEE, 56 samples, AgX,
  look None, exposure −1.1, world background 0.055. **Set `scene.frame_set(1)` before every
  render**: the gate scripts leave the scene on frame 155, and the first P3f front render
  came out aimed at the machine's bottom corner.
- Renders: `review/v13/p3f_front.png`, `p3f_3q.png`, `p3f_top.png`, `p3f_claw.png`.

### Saved

`G:\DSHProject\BlenderMcp\hero_animation_v13_p3f.blend` — 338,746 bytes, 98 objects, 88 meshes,
16 materials, 37 actions, 23,540 triangles, current frame 1, `scene.camera` = `Cam_Hero`. The
seven QA lights and cameras and their data-blocks were deleted before saving.

### Still open after P3f

1. The window frame reads as near-black: `MAT_Window_Frame` base colour is 0.024 and the
   reference frame is a mid charcoal with visible thickness. Material pass.
2. The mint top skin is too glossy — it catches a hard specular from the QA key light and reads
   as plastic film. Also material (roughness), not geometry.
3. The 30 pastel `P2_Nebula_*` spheres inside the window still have no volume. Material pass.
4. `P1_ShoulderBay` is a hard-edged box with no bevel, visible from the back as an ear.
5. The outlet is still a tray with an amber floor and a dark tongue rather than a small rounded
   spout. The tongue is load-bearing for the product path gate, so this stays as a documented
   deviation.
6. `Cam_Hero` plus the two suns still leave the body underlit; the QA rig is the only thing that
   makes the colours readable. Lighting pass, deliberately deferred.

## v13 P3g (2026-11-02) — closing the geometry pass

Small polish so the geometry side can be declared finished. Materials and lighting are still
deliberately untouched.

1. **Bevels on the last two hard-edged parts.** `P1_ShoulderBay` (the cream bay the arm root
   grows out of, 192 verts) had no modifier at all and read as a die-cut box from the back;
   it now carries an angle-limited Bevel of 0.012 / 3. `P1_MintStrip_L/R` were 0.010-thick
   plates with square edges; both now carry Bevel 0.004 / 2, so the mint panel has a soft
   rim instead of a paper edge.
2. **Bolt heads were invisible.** All eight `P1_Bolt_*` sat 0.001 proud of their face, which
   is sub-pixel at any sane render size. The 12 front-most vertices of each bolt were pulled
   to y ±0.806 (0.006 proud). Vertices only — no object transform, no origin, no parent, no
   action touched.

Triangle cost: 23,540 → **24,148 of 25,000** (the shoulder bay grew 372 → 668, each mint strip
76 → 236). Everything else is unchanged: `qa_v2/v13_grab_p3g.json` **PASS** with the same
numbers as P3f to five decimals (f31 L 0.00557 R 0.01118; f147 L 0.01267 R 0.01492; f155
L 0.40271 R 0.45016; overlap 0); `qa_v2/v13_product_path_p3g.json` **PASS** (RESTING 43 / ARC 14
/ EXITED 13 / COLLAPSED 26, negative gaps 0, support ratio 1.0 on every frame);
`qa_v2/v13_shape_metrics_p3g.json` unchanged from P3f; loop closure over all 98 objects at
f1 vs f327 worst delta 0.0, 0 broken; NaN 0; 37 actions.

Renders: `review/v13/p3g_front.png`, `p3g_3q.png`, `p3g_back.png` (the back view is new — it is
the first time the back has been rendered, and it confirms the mint skin stops cleanly at the
top edge and the plinth band reads as one piece around all four sides).

Saved `hero_animation_v13_p3g.blend` — 339,818 bytes, 98 objects, 88 meshes, 37 actions,
24,148 triangles, `scene.camera` = `Cam_Hero`, frame 1, QA rig deleted before saving.

### What is left, and none of it is geometry

Modelling is finished. What remains, in the order the reference punishes us for it:

1. **Materials** (deferred by request): `MAT_Window_Frame` base 0.024 reads near-black instead
   of charcoal; `MAT_Color_Mint` is too glossy on the top skin; the 30 `P2_Nebula_*` spheres
   are flat pastel; `MAT_Window_Cavity` is light grey instead of dark teal.
2. **Lighting** (deferred by request): `Cam_Hero` plus two suns (`SUN_Hero` 3.0, `FILL_Hero`
   0.8, world 0.051) still leaves the body underlit.
3. **GLB re-export** from P3g with `use_visible=True`, after deleting the five scaffolding
   cutters/proxies (`Cutter_Outlet`, `Cutter_Window`, `P1_Cutter_SeatOpen`,
   `Product_Proxy_FitCheck`, `Product_Proxy_Large`).
4. **Documented deviation that will not be fixed**: the outlet tongue is still 2.24 long
   (1.24 of body width) against the reference's 0.677, because `ProductAction.001_V2` slides
   the orb along it and the path gate fails on any shorter version. The cream scoop, seat
   collar and hatch all match the reference; only the structural tongue is long.
5. `window_h_to_w` 1.2972 against the reference's 1.5528 — unreachable, the reference's own
   three window numbers contradict each other (see the P3f unit-trap note).
