# STATUS — hero-blockout / 抓娃娃机资产（main @ `5ae66db`）

**Last updated:** 2026-11-25（§11 方案 2 重建；v14 侧的台账仍停在 11-24 的状态）
**Branch:** `main` · v14 线基线 `5ae66db` "v14 repair pass: outlet, base, screws, claw" (2026-11-04)；方案 2 重建线见 §11（产物 `versions/rebuild_v7_*.blend`，与 v14 线互不覆盖）
**Working tree:** v14 侧原有未提交改动仍在（`M hero_animation_v14_p19.blend` 于 11-08 被另存、若干未跟踪 `.blend`），**本轮未触碰、未提交**。V2 重建的产物见 §10。
`M hero_animation_v14_p19.blend` · 未跟踪 `hero_animation_v14_p7.blend`、`reconstruct.blend`、`hero_animation_v14_p47_hole_f3.blend`、`zhuazhuaji.blend`、`zhuazhuaji_webfix.blend`、`zhuazhuaji_webfix.glb`、`scratch/*`

## 0. Bottom line

| 问题 | 现状（可证实） |
|---|---|
| 最新已提交几何 | `hero_animation_v14_p47_no_rail.blend`（repair pass） |
| 最新 GLB | `hero_animation_v14_p6.glb`（2026-11-02）—— 不含 P18 / P19 / repair 的任何改动 |
| p47 的 GLB | **不存在**，未导出 |
| 未提交改动 | `p19.blend` 于 2026-11-08 19:05 被另存：删 `P1_MintStrip_L/R`、`P3f_TopSkin`，加无材质 `Cube`（动作 36→37）；无文档 |
| 沉孔可见性 | **12/20**：F3 已在 `p47_hole_f3.blend` 开孔；T0–T3、L0–L3 仍被挡（§3.1 / §9-2） |
| 旁支 | `zhuazhuaji*` 是同一场景拷贝后删件 + 从 Desktop append 的 WIP（§5），不是 p47 的后代 |
| 文档 | `BUILD_NOTES.md` 止于 v13 P3h，**v14 零记录**；本文件是 v14 唯一台账 |

一句话：主线停在 p47，但 p47 没有 GLB、也没有对应渲染；最新导出的 GLB 仍是 p6，它不含 v14 后续的任何改动。

## 1. v14 提交链

| commit | date | 内容 | 产物 |
|---|---|---|---|
| `1eac252` | 11-02 | P4 参考锁定比例、材质、出口重建计划 | `p4.blend` / `p4.glb` |
| `da691bc` | 11-02 | P6 出口改为奶油壳 + 琥珀内衬 | `p5.blend`（对照）、`p6.blend` / `p6.glb` |
| `496b454` | 11-03 | P18 出口改为橙色嘴 + 奶油托（越界：67,444 tris） | `p18.blend` |
| `6c21d26` | 11-03 | P19 收回为开放 U 槽 + 奶油领口，拆掉 P18 的回归 | `p19.blend` |
| `92b7ed5` | 11-03 | 四点审计：底座 / 螺丝 / 爪 / 出口 | `review/v14/AUDIT_REVIEW.md` 等 |
| `5ae66db` | 11-04 | repair pass：出口、底座、螺丝、爪 | `hero_animation_v14_p47_no_rail.blend` |

`p5.blend` 并入了 P6 提交，没有单独 commit。

## 2. 文件台账（2026-11-10 实测，Blender 后台只读统计）

### 2.1 v14 blend

| 文件 | git | 大小 | 对象 | 网格对象 | 材质 | 动作 | 备注 |
|---|---|---|---|---|---|---|---|
| `p4.blend` | tracked | 871,210 B | 86 | 71 | 16 | 37 | P4 基线 |
| `p5.blend` | tracked | 896,413 B | 83 | 68 | 16 | 36 | P6 的对照检查点 |
| `p6.blend` | tracked | 897,815 B | 83 | 68 | 16 | 36 | 最后一个出过 GLB 的状态 |
| `p7.blend` | **untracked** | 896,517 B | 83 | 68 | 16 | 36 | 11-02 16:04 另存，无文档；不在提交链上 |
| `p18.blend` | tracked | 873,741 B | 83 | 68 | 16 | 36 | 出口回归版（tris 68,124 全部对象） |
| `p19.blend`（HEAD） | tracked | 877,407 B* | 88 | 73 | 16 | 36 | 审计所用版本；无激活相机 |
| `p19.blend`（工作区） | **M** | 886,884 B | 86 | 71 | 16 | 37 | 未提交 WIP，见 §4 |
| `p47_no_rail.blend` | tracked | 870,177 B | 117 | 93 | 16 | 36 | 主线头部；激活相机 = `OutletCam` |
| `p47_hole_f3.blend` | **untracked** | 873,076 B | 118 | 94 | 16 | 36 | p47 + `P3d_Label` 的 F3 过孔（§3.1） |
| `reconstruct.blend` | **untracked** | 879,126 B | 65 | 50 | 16 | 36 | 11-05 另存，无文档、无激活相机，缺底座/脚 |

\* HEAD blob 877,407 B；工作区被覆盖为 886,884 B（尺寸不同也说明不是单纯的元数据变更）。HEAD 内容用 `git show` 导出到临时文件后统计。

### 2.2 GLB

| 文件 | git | 大小 | meshes | nodes | 材质 | 动画 | 贴图 |
|---|---|---|---|---|---|---|---|
| `v12_style.glb` | tracked | 581,760 B | — | — | — | — | — |
| `v13_p2.glb` | tracked | 857,620 B | — | — | — | — | — |
| `v13_p3b.glb` | tracked | 1,094,460 B | 76 | 83 | 15 | 18 | 0 |
| `v14_p4.glb` | tracked | 1,524,228 B | 44 | 66 | 13 | 12 | 1 |
| `v14_p6.glb` | tracked | 1,577,084 B | 42 | 64 | 13 | 11 | 1 |
| `zhuazhuaji_webfix.glb` | **untracked** | 1,198,796 B | 35 | 56 | 12 | 17 | 0 |

GLB 数字均由解析 GLB JSON chunk 得到；v12 / p2 只核对了体积。

### 2.3 v13 与更早

v13 是 11 个阶段文件（`p1`、`p2`、`p3`、`p3b`–`p3h`、`soft`，250–347 KB），只出过 `p2.glb`、`p3b.glb`；细节留在 git 历史与 `BUILD_NOTES.md`，不在此重复。v13 的"最新交付物"已不是 p3b（见 §8）。

## 3. 已证实的量化指标（p47，repair pass 后）

| 项 | 值 | 来源 |
|---|---|---|
| 三角面 | **26,424**（audit，f240；预算 60,000） | `qa_v2/v13_baseline_audit.py` 复跑 |
| 动画 | 36 actions / 146 fcurves / 3,324 keys，loop 端点差 **0.0** | 同上 |
| 底座实体率 | **0.90241**（bbox 1.80 × 1.56 × 0.268，z 0.02–0.288；scale 已归 1） | bmesh 体积复测 |
| 底座脚嵌入 | `Machine_Feet` z −0.10…0.02，即嵌入底座 **0.02** | bbox 复测 |
| 溜槽法线 | 有符号体积 **+0.090418**（朝外）；bbox x 0.86–2.30 / y ±0.415 / z 1.039–1.556 | bmesh 复测 |
| 出口贯穿 | 机身壁已切开：从 x 0.80、0.85 向 +X 的射线在 z 1.10/1.30 全部逸出；内端由琥珀 `P1_BoreBack`（x 0.66–0.72）封住，顶部有 `P1_BoreLinerTop`（z 1.432–1.452） | 射线复测 |
| 领口位置 | 奶油领口 bbox x 2.22–2.32、y ±0.52、z 0.97–1.597（已在嘴部）；`P1_ChuteRail`、`P1_ChuteSeat`、`P1_BaseBand`、`P2_OutletBand`、`P1_Bolt_*` 均已移除 | 对象表 |
| 螺丝 | 0 个螺栓实体；20 个 `Cutter_Screw_{B,F,L,R,T}{0-3}` 已布尔切入机身；开孔后 **12/20** 可见（§3.1） | 对象表 + 轴向射线 |
| 爪硬件 | 12 件（`Arm_Finger_{L,R,C}_{cuff,pin,washerA,washerB}`），全部父级 `Arm_Wrist`；cuff=琥珀，pin/washer=深色 | 对象表 |
| 产品路径 | PASS：0/96 帧穿透，首帧逸出 f289，弧顶间隙 0.3901 @ f263 | `v13_product_path_gate.py` 复跑 |
| 穿透 | PASS：0/96 帧（`P1_ChuteSeat` 已删，gate 对其跳过） | `v13_penetration_check.py` 复跑 |
| 抓取 | PASS（v13 gate 口径）：f31 L 0.00645 / R 0.00853，指尖间距 0.2371 | `v13_grab_gate.py` 复跑 |

p19（审计版，供对照）：24,612 可见三角面、36 actions、抓取 0.2531/0.2560（尖到球心口径）、loop 0.000 —— 见 `review/v14/p19/P19_REPORT.md`。

### 3.1 沉孔可见性（`p47_hole_f3.blend`，轴向射线）

沿每个 cutter 轴线从外部射入，跳过不参与渲染的 `Cutter_*`，取第一个实体命中：

| 组 | 命中 | 结论 |
|---|---|---|
| B0–B3 / R0–R3 | `Machine_Body` | 可见 8 |
| F0–F2 | `Machine_Body` @ y −0.784 | 可见 3 |
| F3 | `P3d_Label` 过孔 → `Machine_Body` @ y −0.784 | **新开孔**，可见 1 |
| L0–L3 | `P1_MintStrip_L` @ x −0.912 | 被挡 4 |
| T0–T3 | `Machine_Hopper` @ z 3.4447 | 被挡 4 |

F3 孔：r 0.015（等于沉孔口半径）、与 cutter 同轴、贯穿 4.5 mm 标签；标签太薄，放不下 class C 0.012 倒角，孔边保留直角。标签 bbox 未变，孔壁用 `MAT_Label`，tris 26,684（较 p47 +260，含新 cutter）。

另核实：20 个 cutter 里只有 B/L 两组是口大腔小（r 0.031 在表面）；F/R/T 三组方向相反（r 0.015 在表面、0.031 在 16 mm 深处），从外面看到的是 30 mm 口。F3 的孔按 30 mm 口开，尺寸一致；其余未改。

## 4. 未提交的 p19 改动（WIP，不可当基线）

disk 上 `p19.blend`（11-08 19:05）相对 HEAD 的实测差异：

- 删除 `P1_MintStrip_L`、`P1_MintStrip_R`、`P3f_TopSkin`；
- 新增 `Cube`：144 verts / 270 tris，**无材质**、无修改器、父级为空，location 有 27 个关键帧（`CubeAction`，因此动作 36→37）；
- 激活相机从"无"改为 `Cam_Hero`；
- 规模：86 对象 / 71 网格对象 / 27,018 tris（audit），HEAD 为 88 / 73 / 27,344（raw）。

没有对应脚本、日志或提交说明。**该文件的渲染状态未验证**：`Cube` 无材质，其包围盒（x ±0.931 / y ±0.799 / z 0.417–2.702）正好套住机身下部。

## 5. `zhuazhuaji*` 支线判定：另起一支，不是主线替换

证据（全部可复现）：

1. **同一场景**：`p19` / `p47` / `zhuazhuaji` / `zhuazhuaji_webfix` / `reconstruct` 的 scene `uuid` 都是 `0c0915f9-5824-4d97-953c-c2faf89ffc66`，同一来源的拷贝。
2. **只删不加**：`reconstruct.blend` = p19 工作区 − 21 个对象（`Machine_Base`、`Machine_Feet`、16 个 `P1_Bolt_*`、`P1_ChuteRail`、`P1_OutletCollar`、`Cube`），无任何独有对象。
3. **继续删件**：`zhuazhuaji.blend` 在 p19 基础上又缺 `Arm_Base`、4 个接缝环、`Machine_WindowCavity`、`P2_Plasma` / `P2_Plasma_Back`、`P1_ShoulderBay`、`P1_OutletCollar`、`P1_OutletRailL/R`、`P2_OutletBand`、`Machine_Chute`、`P1_Bolt_R0`；材质 16→13，动作仍是 37（含 `CubeAction.001`）。
4. **append 痕迹**：`zhuazhuaji_webfix.blend` 多出 `Cube.001`、`Cylinder`、`Cylinder.001`、`Arm_Shoulder_Joint.001`（均无材质，`Cylinder` 带 Mirror），以及 `MAT_Arm.001` / `MAT_Arm_Dark.001` / `MAT_Body.001` / `MAT_Product2.001` 与 6 个重复 action；`scratch/zhuazhuaji_audit/webfix_restore.py` 明确从 `C:\Users\Administrator\Desktop\zhuazhuaji.blend` append。删件还带走了动作：37→22。
5. **没有 repair 成果**：`zhuazhuaji*` 里没有任何 p47 新增件（20 个沉孔切刀、12 个爪硬件、10 个出口件、`P1_BoreBack`），`Machine_Chute` 在 webfix 里是 32 verts / 48 tris 的方盒（MAT_Body），不是琥珀 U 槽。
6. **GLB 落后于 blend**：`webfix_export.py` 10:20 导出 GLB → `webfix_restore.py` 11:01 append → 11:02 保存。GLB 里没有 4 个 WIP 对象（`Cube.001` / `Cylinder` / `Cylinder.001` / `Arm_Shoulder_Joint.001`），材质 12 vs blend 17、动画 17 vs blend 22、mesh 35 vs blend 57 个网格对象；即 **GLB 不是当前 blend 的导出**。

结论：这是从 p19 工作区拷出、删掉成品件、再从 Desktop 补件的 **web 向旁支**，几何上不能替代 p47（缺底座/脚/出口唇/爪硬件，溜槽是方盒）。

**待确认**（仓库内无法证实）：这条支线要解决的"web"问题是什么、是否要合并回主线、由谁维护 —— 只有 `scratch/zhuazhuaji_audit/*.py` 脚本，没有说明文档；`zhuazhuaji.blend` 源文件在 Desktop，不在仓库。

## 6. 工具与流程注意事项（v13 实测，至今仍适用）

- Blender：`G:\Blender\blender-5.4.0-alpha\blender.exe`（5.4.0-alpha）。重大改动走 live session + MCP；本文件数字全部来自 `--background` **只读**加载。
- GLB 导出用 `use_visible=True`：`Machine_Light_01/02/03`、`Machine_LightStrip` 从 P3e 起就是隐藏件（参考图里没有），不隐藏会重新出现在 GLB；导出前先删脚手架 cutter/proxy。
- `--background` 的 depsgraph 会过期：`frame_set` 之后读 `obj.evaluated_get(dg).matrix_world`；三角面要在对象可见的帧上量（f155 处 `Product` 被缩到 0.001，会少数 96 tris）。
- QA 渲染的 view transform 决定颜色结论：早期 `Standard` 把奶油打到 #FFF（前视图主体 25.8% 像素），改 AgX 之前的所有颜色判断作废。
- 焊接接缝 + Bevel 会自交，让重叠检测虚报（曾差 7 帧）；用"零件下沉 5 mm"解决，不要靠三角化"修"检测门（曾把干净文件报成 27 帧）。
- `BVHTree.FromObject` 不认父级变换，父级挂件要用世界空间树（`qa_v2` 门禁已按此实现）。
- 给有父级的对象按世界坐标写 mesh 会静默位移，需用 `matrix_world.inverted()` 回局部空间。爪最敏感：`Arm_Finger_L/R`、`Arm_Gripper` 的 `matrix_parent_inverse` 都不是单位阵。
- 退化面在 Bevel 后变 NaN，glTF 导出直接失败（`ValueError: cannot convert float NaN to integer`）；先 `remove_doubles(1e-5)` + `dissolve_degenerate(1e-6)`，并且要查 evaluated mesh，raw mesh 看不出来。
- 审计/门禁脚本在 `qa_v2/`，输出写 `qa_v2/*.json`；每步另存新 `.blend`，不要覆盖（`p19.blend` 就是被原地覆盖的）。

## 7. 复现本文件数字

```powershell
$B = "G:\Blender\blender-5.4.0-alpha\blender.exe"
$F = "g:\DSHProject\BlenderMcp\hero_animation_v14_p47_no_rail.blend"
& $B --background $F --python qa_v2\v13_baseline_audit.py  -- --out $env:TEMP\a.json
& $B --background $F --python qa_v2\v13_product_path_gate.py -- --out $env:TEMP\b.json
& $B --background $F --python qa_v2\v13_penetration_check.py  -- --out $env:TEMP\c.json
& $B --background $F --python qa_v2\v13_grab_gate.py          -- --out $env:TEMP\d.json
```

GLB 计数：直接解析文件头的 JSON chunk（meshes / nodes / materials / animations / images）。

## 8. 旧台账的更正与缺口

**已更正/收敛**
- "最新 GLB 交付物 = `v13_p3b.glb`" 已过期 → 现为 `v14_p6.glb`，但也不是 p47 的导出。
- P4 那一格混着 1.39 MB / 45 meshes / 52 nodes / 11 materials 等中间值，只有最后一组与文件一致：1,524,228 B / 44 / 66 / 13 / 12 / 1。现在只保留最终值。
- 原 §3 的 invariants（机身 1.8000/1.8000、24,464 tris、37 动作、抓取 0.00557/0.01118）是 **v13 P3h** 口径，v14 已改（机身 2.46 高、预算 60,000、36 动作），不再作为检查线；改为 §3 的 p47 实测。
- 原 §6 "what is next"、§8 "open questions" 是 v13 遗留（爪/溜槽），已删除，见 §9。

**缺口（显性登记，未补圆）**
1. p47 无 GLB；`review/v14/` 下也没有 repair pass 的渲染（只有 p19 与 audit 的图）。
2. 沉孔可见性 **12/20**：F3 已由 `p47_hole_f3.blend` 在 `P3d_Label` 上开同轴过孔（§3.1）。其余 8 个仍被挡：
   - T0–T3：`Machine_Hopper` 外沿在 z 3.4447 遮住，沿 −Z 要穿约 58 mm 的漏斗壁；在盛球面开孔会破坏语义，未做。
   - L0–L3：`P1_MintStrip_L` 厚 22 mm，倒角后外表面只到 y ±0.6141；螺钉在 y ±0.6，只剩 14.1 mm 半径，而沉孔口半径 31 mm，开孔会切掉薄荷条边角。
   备选做法见 §9-2。
3. 爪的三指 **120° 等分未做**（`exec/EXECUTION_PLAN.md` 待办），repair 只换了指环、加了铰链硬件。
4. 底座仍是圆角方板 + 倒角，参考的"碗形内收弧"未做（待办）。
5. 爪/出口改完后动画没有重排（p47 与 p19 同为 36 actions，提交说明也未提动画）；`EXECUTION_PLAN.md` 待办里的"张开→抓球→进料口释放"仍未做，抓取姿态只过了 v13 门禁口径（f31 L 0.00645 / R 0.00853）。
6. `BUILD_NOTES.md` 无 v14 记录；`exec/EXECUTION_PLAN.md` §6 的执行日志只到 11-03 的"第一轮"（0–4 阶段，阶段 4 标"⚠️ 未完成"），没有阶段 5/6 的记录，而 11-04 的 `5ae66db` 已经做了爪硬件、出口、螺丝 —— 日志停留在它之前，按提交和文件为准。
7. `qa_v2/p47_gate.json`、`qa_v2/p47_pen.json` 里记的绝对路径是 `G:\DSHProject\hero-blockout\...`，不是当前 `g:\DSHProject\BlenderMcp`；内容与复跑结果一致，但路径对不上。
8. `p7.blend`、`reconstruct.blend`、`zhuazhuaji*` 全部未跟踪且没有任何说明；`scratch/*.txt`、`scratch/*.json` 是过程日志/探针输出，不是可审阅的文档。

## 9. 待用户裁决

1. p47 是否就是 v14 主线的收口？要不要为它导出 GLB / 补渲染。
2. 沉孔可见性：F3 已完成。T0–T3 / L0–L3 需要选：
   - T：把 hopper 外沿收小或抬高，或把 4 枚顶螺钉移到 hopper 外；或接受 4 枚为内部紧固件（16/20）。
   - L：在薄荷条孔位加宽/加圆形凸台（保留 class C 倒角），或把 4 枚侧螺钉内移到 y ±0.55；或接受在薄荷条边缘开缺（不推荐）。
3. `p19.blend` 工作区的 `Cube` 改动是继续还是丢弃（当前它未提交、无材质）。
4. `zhuazhuaji` 支线：并入主线、独立发布，还是弃用；源文件在 Desktop 需要纳入仓库吗。

## 10. V2 重建（2026-11-23 / 11-24）—— 从 Tripo 参照反推低模 + 复用 p19 动画

**目标**：用 Tripo 生成的 triangulate 参照（`ReferenceModel.blend`，43 件 mesh / 2,411 v / 2,929 tris / 100% 三角面 / 无骨架无动画）反推一套拓扑更好的低模，并把 `hero_animation_v14_p19.blend` 的既有动画原样接上。

**做法（B′）**：不重建骨架，`bpy.ops.wm.open_mainfile(p19)` 后**原地替换 mesh datablock**——对象 / 父子 / `matrix_parent_inverse` / action / 约束 / 枢轴一个都不动，动画因此天然对齐；只有网格是新的。

**尺度冲突与取舍**：Tripo 主体 1.000 宽 × 0.754 高，p19 主体 1.800 宽 × 2.460 高，机械臂伸展 x −3.02 vs −0.41（7.4×），宽高比甚至相反。动画位移是绝对量，字面照 Tripo 建会让机械臂转 90° 时爪子伸不出机壳。故落成 B′：**绝对尺寸与枢轴位置全部照 p19，只搬 Tripo 的造型语言**（圆角半径、曲率、分割线、格栅、配色）。代价是整体比 Tripo 高瘦，这是约束的结果而不是建模失误。

**产物**

| 文件 | 内容 |
|---|---|
| `rebuild_v2.blend` | 正式工程，可直接打开播放 1–327 帧 |
| `versions\rebuild_t1.blend` | T1 首版（出料口过长、铭牌过小，已否决，留档） |
| `versions\rebuild_t1b.blend` | T1 修正版（放行） |
| `versions\rebuild_t2.blend` | 与 `rebuild_v2.blend` 字节一致（导出前快照） |
| `export\hero_v2.glb` | 交付 GLB，1,166,580 B / 58 nodes / 28 clips / 1–327 帧 @60fps |
| `versions\rebuild_t1b_report.json` / `rebuild_t2_report.json` | 每步的量化验收记录 |

**网格口径**

| 资产 | verts | tris | 四边面 |
|---|---|---|---|
| Tripo 参照 | 2,411 | 2,929 | 0（全三角面） |
| p19 原资产 | 11,918 | 23,150 | 10,532 |
| **V2 重建** | **8,175** | **16,050** | **92.0%** |

**动画门禁**（`scripts\verify_anim.py`，17 个动画对象 × 8 帧 = 136 采样点，逐点比对 `matrix_world` 的位移/欧拉/缩放，阈值 1e-4）：

```
VFRAME 136  mismatched=8  worst_delta=0.03248000
```

8 个不一致点**全部**是 `Machine_Hopper`——它的对象 scale 从 p19 的 `(1.0325, 1.0325, 1)` 归一成 `(1,1,1)`，世界半径直接烘进剖面。外观与动画路径完全一致，只有对象局部缩放值与 p19 不同。其余 128 点 delta = 0。

**两个导出事实（踩过，记下来）**

1. glTF 没有可见性通道。`Product` / `Idea` 的 `hide_render` 驱动显隐，导出前被烘焙成 scale 通道（隐藏帧 1e-4 而非 0，避免退化矩阵；对半径 0.5 的球是 5e-5 单位，亚像素）。`Product` 作者意的 f300 `(0.7, 0.7, 1.0)` 保留。烘焙只在导出进程内存里做，`rebuild_v2.blend` 不回写。
2. **`Machine_Body` 在源文件里 `hide_get()==True`**（大纲视图那只眼睛），`hide_render` / `hide_viewport` 却都是 False。glTF 导出器在 `use_selection=True` 下会整颗丢弃 `select_get()==False` 的对象——于是**主壳体长期以来从未进过任何 `hero_v2.glb`**，而它的 4 个配件被当成根节点导出，等于"有字无身"。已在 `scripts\export_glb.py` 修掉：导出前对 `hide_render` 与 `hide_viewport` 同为 False 的 mesh 清一次 outliner 眼睛，恢复的恰好只有 `Machine_Body`（+1 节点，57→58）。

**已知未圆**

1. 珊瑚端帽是实心圆角块，不是参考图那种"奶油鼻 + 细珊瑚包边"——在"托盘止于 x=2.60 / 护栏止于 x=2.88"的约束下，单件只能是实心盖。
2. 铭牌字标是四块胶囊压印条，读得出"有个标"，读不出字母（不用真字体转网格的代价）。
3. 整体比 Tripo 高瘦（见上，动画约束所致）。
4. `Machine_Hopper` 的对象 scale 与 p19 不同（外观与动画一致，只是局部缩放值）。
5. `Machine_Light_01/02/03/LightStrip` 与 `Arm_Mount` 被有意排除在 GLB 之外（沿用 `use_selection=True` 口径，未切 `use_visible`），它们身上的 color 动画因此不在 GLB 里。

**复现**

```
blender.exe -b --python scripts\build_v2.py -- 4      # 从 p19 重建全部网格 -> rebuild_v2.blend
blender.exe -b --python scripts\verify_anim.py        # 动画门禁
blender.exe -b --python scripts\export_glb.py         # 烘焙可见性 + 导出 GLB
blender.exe -b --python scripts\validate_glb_vis.py   # 回导校验
blender.exe -b --python scripts\anim_sheet.py -- 'G:\DSHProject\BlenderMcp\renders\anim' 4
```

`build_v2.py` 是幂等的：每次运行都从 p19 重新打开，`-- <stage>` 控制建到第几阶段。`render_compare.py` 的 outdir **必须是绝对路径**，相对路径会静默不写盘。
### 10.1 源文件更正：p19 工作区那笔未提交改动（11-24）

`hero_animation_v14_p19.blend` 的工作区里压着一笔**本次会话之前**的未提交改动（11-08 另存，877,407 → 886,884 B）。实测差异：

| | HEAD（已提交） | 工作区（未提交） |
|---|---|---|
| `Machine_Body` | `hide_get=False`，192 verts | `hide_get=True`（大纲眼睛闭着） |
| `P1_MintStrip_L` / `_R` | 存在（40 / 16 verts） | **已删除** |
| `P3f_TopSkin` | 存在（128 verts） | **已删除** |
| `Cube` | 无 | **新增**，144 verts，1.861 × 1.598 × 2.285，无材质 |
| actions | 36 | 37 |

即：把真壳藏起来、删掉两条侧薄荷条和顶皮、在壳的位置塞一个裸立方体——用户确认是被放弃的"换壳"试验。

处理：`git checkout -- hero_animation_v14_p19.blend` 还原到 HEAD（88 对象 / 36 动作 / `Machine_Body` 可见）；失败品留存未跟踪副本 `scratch/p19_failed_bodyswap_2026-11-08.blend`。`scripts\build_v2.py` 现在**显式删除** `Cube`、`P1_MintStrip_L/R`、`P3f_TopSkin` 与 16 颗螺钉（它们都已被重建的壳 / `V2_SidePanel` 取代），因此对两种 p19 状态都产出同一个模型。

用还原后的 p19 重跑验证：`verts=8175 tris=16050 faces=7899 quads=7271 quad_share=92.0%`、`VFRAME 136 mismatched=8 worst_delta=0.03248000`（8 条全 Machine_Hopper）——与提交前的数字**逐项一致**。GLB 重导 1,166,580 B、`outliner_unhide=[]`（说明 §10 那条丢壳修复现在只是防御性代码，真正的原因是这笔改动），`validate_glb_vis.py` 仍 `PASS`。

注：`versions\rebuild_t2.blend` 是旧 `rebuild_v2.blend` 的字节副本，与现版在 provenance 上不同（几何与动画一致），保留作为当时的快照记录。

## 11. 方案 2 重建（2026-11-24）—— 参照绝对尺寸 1:1 + 动画重编

**与 §10 的关系**：§10 是路线 B′（原地换 mesh，动画零风险，代价是高瘦）。本轮用户裁决改走**方案 2**：按参照的绝对尺寸重建、动画重编。完整待办见 **`REFERENCE_REBUILD_PLAN.md`**。本节只记已完成的部分。

**裁决依据**（用户原话）："动画其实我只是要那种抖动和表现，其实也不用完全一样，不如我们分步做，先把模型做出来，在做动画"。面数目标："越低越好，大概 3K 左右"。

**为什么不能等比放大**：参照箱体高/宽 = 0.78，v14 = 1.37；参照臂长/箱宽 = 0.57，v14 = 1.67。高宽比与臂身比都相反，是两种设计而非两种尺度。

**产物**

| 文件 | 内容 |
|---|---|
| `versions\rebuild_v7_s1.blend` | **Stage-1 基线**（体块与比例，0.13 MB）；自 2026-11-25 起为**冻结输入资产**，sha256 `c9b647bf…` |
| `versions\rebuild_v7_s2a.blend` | **Stage-2a**（删 17 张真埋端盖），2,178 tris / 27 ngon，131,203 B |
| `ReferenceModel.blend` | 参照原件（Tripo，43 件 / 2,929 tris），sha256 `b1b11d85…`；2026-11-25 入库（此前一直未进 git） |
| `qa_v3\topo_freeze.py` | 冻结契约：`init/check` 守输入哈希，`objects/diff` 守拓扑指纹（S2.6 那道门） |
| `renders\v7_s1\v7_{front,right,top,iso,armclose}.png` | 五视图，workbench / material 色 / cavity BOTH / AA 16 / ortho_scale 1.15 |
| `renders\ab_v7\` / `renders\ab_s2a\` | S2.5a 的 A/B 五视图（同脚本同相机，用于逐像素证明） |
| `reference\v4_rigspec.json` | 建模基准：关节坐标 + 箱体/料斗/滑道实测尺寸 |
| `reference\parts_20261124.json` | 参照 43 件的逐件 bbox 全表 |
| `reference\contract_20261124.json` | v14 动画契约全表（36 action / 通道 / 关键帧采样） |
| `reference\views_20261124\` | 参照的 7 张对照渲染（`ref_*` 与 `arm_*`） |

**Stage-1 实测**（`rebuild_v7_s1.blend`）

| 项 | 参照 | v7 | 差 |
|---|---|---|---|
| tris | 2,929（100% 三角面） | **2,352** → 2a **2,178** → 2c **2,322** | −20% → −26% → −21% |
| quads | 0 | **920** → 2c **984** | — |
| ngon | 0 | 44 → **27**（S2.5a 删掉 17 张真埋端盖；余下 27 张是露着的平面端盖，按 Plan B 留到导出时三角化） | 见 §11.1 / §11.2 |
| 对象 | 43 散片 | **39** → 2c **41** 命名件（删 5 片浮散热栅 + 7 片鳍） | — |
| bbox | x −0.501..0.500 / y ±0.231 / z 0..0.754 | x −0.468..0.496 / y −0.235..0.231 / z 0..0.769 | x_min 短 33 mm（臂根外移，S2.3）；z 高 15 mm 的来源是 `Arm_UpperArm` 管顶 0.768，**不是爪尖**（2026-11-25 更正） |

**中途否决的三版**（`rebuild_v3/v4/v5_s1.blend` 留档）：v3 料斗是实心盘子（`primitive_cone_add` 默认封顶）、臂杆半径 0.03 太细、爪子按 Y 轴展开在前视图叠成一根尖刺；v4 改粗臂改有改善；v5 换三指 120° 爪；v6 料斗改 bmesh 旋转壳但内壁给了 `M_Rubber` 近黑；v7 内壁改 `M_ShellDk` 定稿。

**未圆**（已在计划里排期）：滑道缺侧壁起伏（S2.2）、爪指偏瘦且只有 3 根（S2.3）、面板凹边直角（S2.4）、无 UV（S2.6）、材质为占位色（S2.7）、未导出（S2.8）、动画未开始（Stage-3）。背面散热栅（S2.1）与料斗剖面（S2.1b）已于 2026-11-25 完成，见 §11.2。

### 11.1 S2.0 冻结与 S2.5a 执行（2026-11-25）

**三件裁决**（用户原话 m00384：「1按你推荐，2的话入git，3的话对角驱动」）：v7 定为冻结输入资产不补写 builder、`ReferenceModel.blend` 入库、手指按对角映射（`Finger_L`→A+D、`Finger_R`→B+C）。

**冻结哈希**（`qa_v3/topo_freeze.py init` 产出，`check` 已复验）：`ReferenceModel.blend` = `b1b11d856509ad19…`（2,374,068 B）、`versions/rebuild_v7_s1.blend` = `c9b647bf15344eb8…`（131,685 B）。任何重建命令必须先过这道哈希。

**S2.5a 结果**

| 指标 | v7_s1 | v7_s2a |
|---|---|---|
| triangles | 2,352 | **2,178** |
| quads | 920 | 920 |
| ngons | 44 | **27** |
| polys | 1,100 | 1,083 |

删的是 17 张 enclosure=1.00 的端盖：`Arm_Riser`×2、`Arm_UpperArm`×2、`Arm_Base`、`Arm_Forearm`、`Arm_WristCollar`、`Chute_Foot_0/1`、`Machine_Feet_0..3` 顶、`Machine_HopperNeck`×2、`P3d_HopperCollar`、`P3d_TopDisc`。

**可见性不是判断是测量**：`scripts/render_views.py` 同契约渲两版五视图，`scripts/ab_diff.py` 逐像素比对 → front/top/iso/armclose **0 px**，right 仅 **5 px**（max 3/255，是开孔后边缘抗锯齿的一丝漏光）。

**判定的实现只有一处**：`scripts/cap_occlusion.py`（面心 + 8 内点 × 9 根 70° 锥射线，全部采样命中才算埋住）。此前两次判定都错：bbox 包含法、以及"面心单点射线"法——后者把 `Arm_Base` 上环（encl 0.33）与 12 张共面指节盖（0.33–0.78）误判成埋住，照单删会删出破口。

**给 S2.1b 留的坑**：沿斗轴射线的实测显示，斗口向下第一层命中的是 `P3d_HopperCollar` 的顶盘（z 0.4878），它正挡在被删掉的颈部双盖之上，所以画面没变。§4.3 把领口收到 r 0.080 / 压到 z ≤ 0.472 时这块盘就没了 → 必须同一次改里显式决定斗底（保持真漏斗开口，或补一张 z 0.462 的底盘），并重跑分诊 + A/B。

### 11.2 S2.1 背面散热栅 + S2.1b 料斗剖面（2026-11-25）

链条：`rebuild_v7_s2a.blend` →（`scripts/s2_1_vents.py`）→ `rebuild_v7_s2b.blend` →（`scripts/s2_1b_hopper.py`）→ **`rebuild_v7_s2c.blend`**。每一步都过 `scripts/stage_lock.py` 的链式哈希。

**S2.1 散热栅**：v7 的 5 片浮片整组埋在实心箱体里（y 0.199–0.2112 vs 背面 0.231），一次背面都没渲过所以没暴露。做法是删掉箱体唯一那张 +Y 四边形、用它的角 + 洞口角重建 **4 张边框四边形**，再向内拉 41 mm 出 4 壁 + 底（9 张四边形换 1 张，全四边、无布尔）；7 片鳍高 8 mm、贴槽底、留 6.7 mm 缝（照参照的 24 mm 高会叠成一块整板，第一版渲出来就是一片死板）。

**S2.1b 料斗**：§4.3 记的"领口穿出内壁"只是症状 —— 真因是漏斗外壁斜率 0.783、内壁 0.898，二者在 z≈0.532 交叉，其上管壁自交、内外颠倒（z 0.49 处径向首个命中的是外壁 0.0919，比内壁 0.1085 还近）。按参照的实测内外壁重做 5 点闭环剖面，恒 ~12.5 mm 壁厚，斗底压到 z 0.445 藏进箱体 3 mm。领口尺寸一字未动，r 0.088 现在完整地缩在内壁里。

| 指标 | s2a | s2c |
|---|---|---|
| triangles | 2,178 | **2,322** |
| quads | 920 | **984** |
| ngons | 27 | 27 |
| objects | 39 | **41** |
| IoU front / right / top | 0.8744 / 0.8900 / 0.9101 | **0.8843 / 0.9048 / 0.9081** |

**可见性照旧是测的**：S2.1 加进去的 16 个三角在 front/right/top/iso/armclose 五视图上 **0 px**，只在新增的 `back` 视图（24,580 px）与 `ventclose` 上可见。

**遗留**：`Machine_HopperNeck`（20 polys）现在整只落在新漏斗壳体内、已不可见，留给 S2.5b 用遮挡判定正式删；`P3d_HopperCollar` 仍是实心柱（参照是空心环），但它的内腔在闭合壳体里、任何视角都看不到，不单独处理。

### 11.3 S2.3 机械臂重做：四指 + 臂根 loft + 压肘（2026-11-25）

链条：`rebuild_v7_s2c.blend` →（`scripts/s2_3_arm.py`）→ **`rebuild_v7_s2d.blend`**。关节契约随之升级为 `reference/v5_rigspec.json`（Stage-3 以它为准，不是 v4）。

**三处改动**
1. **爪 3 → 4 指**。计划原定"绕腕轴 90° 等分"，实测否掉：腕轴 ≈ (0.994, 0.016, −0.110)，绕它的环垂直于前视方向，4 个 90° 投到前视只剩两根；而 `arm_front.png` 里是四根分明。改成 **XZ 面内的扇**（phi −45/−15/+15/+45，根部 0.016 → 中节 0.0115 → 末节 0.007，三角扇封口）。A..D 仍按左→右命名，`Finger_L→A+D`、`Finger_R→B+C` 的语义不变。
2. **臂根 `Arm_Riser` 重建为 4 环 loft**。第一版直接拉宽到 0.176 读起来像斜插的刀片。改用 `scripts/s2_3_silhouette_rows.py` 把参照前视蒙版逐行换算回世界米，量到左缘 z 0.50→−0.4349、0.55→−0.4589、0.60→−0.4877、0.65→−0.4956（越往上越外），据此定环高 z 0.4455/0.5200/0.6000/0.6820、左缘 −0.4300/−0.4400/−0.4877/−0.5005、bevel 0.014/3 段。
3. **压肘**：超 15 mm 的是 `Arm_Elbow_Joint` 那团球（r 0.044 @ 0.725 → 0.769），不是上臂管。肘降到 0.709 → 冠顶 0.753；腕留 0.706、前臂盒下移 9.4 mm；`Arm_Gripper` 抬高 10 mm（在 x −0.12 列补上 25 mm 缺口）。

| 指标 | s2c | s2d | 参照 |
|---|---|---|---|
| triangles | 2,322 | **2,734** | 2,929 |
| quads | 984 | **1,154** | — |
| ngons | 27 | **15** | — |
| objects | 41 | **43** | 43 |
| `x_min` | −0.468 | **−0.4983** | −0.5005 |
| `z_max` | 0.769 | **0.753** | 0.754 |
| 指簇 x | — | −0.2005..−0.0995 | −0.19..−0.10 |
| 指簇 z | — | 0.6094..0.6881 | 0.62..0.71 |
| IoU front / right / top | 0.8843 / 0.9048 / 0.9081 | **0.8855 / 0.9065 / 0.9177** | — |

**没做到的（记在这里以免下次重新发现）**：front 只涨 0.12 点。逐行比对显示剩余差异不在臂上——z 0.30/0.40 两行我们的箱体右缘到 0.0969，参照只到 0.0714/0.0730（23–26 mm，参照箱体右侧是收进去的）；z 0.60 一行参照在 x −0.1634 还有东西。这两处归 S2.2/S2.4 与箱体形体，S2.3 不动。指簇整体比参照低 12–16 mm，要补应上抬腕链而不是加长手指。

### 11.4 S2.3b 形体补差 + S2.2 滑道（2026-11-25）

链条：`s2d` →（`scripts/s2_3b_body_fingers.py`）→ **`s2e`** →（`scripts/s2_2_chute.py`）→ **`s2f`** = 当前最新。§11.3 末尾那两条"没做到"按用户选的 A 路线补完了。

**两处都先量后改，两次都被"bbox 不等于实体"咬到**

1. **箱体右墙带拔模**。对 `tripo_part_0` 从 x=+0.60 打射线（`scratch/probe_body_profile.py`）：y=±0.15 处墙的 x 是 z 0.04→0.0616/0.0619、z 0.20→0.0701/0.0706、z 0.40→0.0723/0.0738，约 **1.2° 拔模**；我们那面是笔直的 0.0969，**每个高度都宽 23–26 mm**。改法：右侧倒角环**刚性平移 24.5 mm**（`x ≥ 0.0499` 共 48 顶点）。只推平的那张四边形会自交——24.5 mm 超过倒角半径 48 mm 的一半。
2. **指簇上抬**：四指 +18 mm、`Arm_Gripper` +10 mm。不一起抬 18 mm 的原因：gripper 顶会到 0.755，反超肘球 0.753。
3. **滑道深度**：`tripo_part_7` 的 bbox 0.2446 是含凸起的外包，从上往下打 y 阶梯测出真实 footprint 只有 **0.232**（`scratch/probe_chute_footprint.py`）。第一次按 bbox 拉到 0.2446，顶视 IoU **掉了 0.0024**；改回实测 0.232 后三视全正。导轨 `P1_OutletLip_L/R` 同时从"骑在滑道外缘"移到参照实测带 y −0.138..−0.117 / +0.059..+0.083。
4. **S2.4 判定不做**：`Machine_WindowFrame` 对 `tripo_part_6` 差 ≤0.2 mm，凹深 11.5 mm 已在；剩余只是内屏边框 1–2 mm 圆角，627 px/m 下不足 1.5 px。

| 指标 | v7_s1 | s2f |
|---|---|---|
| triangles | 2,352 | **2,734** |
| quads / ngons / objects | 920 / 44 / 39 | **1,154 / 15 / 43** |
| IoU front | 0.8751 | **0.8919** |
| IoU right | 0.8903 | **0.9064** |
| IoU top | 0.9059 | **0.9273** |

产物：`versions/rebuild_v7_s2e.blend`、`versions/rebuild_v7_s2f.blend`、`renders/ab_s2e/`、`renders/ab_s2f/`（各 7 视图）、`scripts/s2_3b_body_fingers.py`、`scripts/s2_2_chute.py`。