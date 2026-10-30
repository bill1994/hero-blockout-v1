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
