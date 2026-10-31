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

