# REFERENCE_REBUILD_PLAN — 参照 1:1 低模重建 + 动画重编

**建立日期：** 2026-11-24
**状态：** Stage-1 已完成并入库；Stage-2 / 3 / 4 待做
**上游台账：** `STATUS.md` §10（路线 B′ 的结论与缺口）、§11（本计划的 Stage-1 记录）
**目标文件：** `versions/rebuild_v7_s1.blend` → 后续 `versions/rebuild_v8_s2.blend` … → `rebuild_v3_final.blend`

---

## 0. 一句话

把 Tripo 生成的 43 件全三角参照（`ReferenceModel.blend`）**按绝对尺寸 1:1 重建**成四边面为主的低模（≤3,000 tris），**动画不迁移、按新枢轴重编**——只保留 v14 的节奏骨架与"抖动和表现"。

这与 §10 的路线 B′ 是两条不同的路：

| | B′（§10，已完成） | 本计划（方案 2） |
|---|---|---|
| 尺寸基准 | p19 / v14 的绝对尺寸（主体 1.800 × 2.460） | **参照的绝对尺寸**（主体 0.534 × 0.419） |
| 网格来源 | 原地替换 mesh datablock | 全新对象树，按参照实测尺寸建 |
| 动画 | 原样保留（世界矩阵 128/136 点 delta=0） | **重编**（枢轴全换） |
| 结果 | 16,050 tris / 92% 四边面 / 动画零风险 | 目标 ≤3,000 tris / 参照轮廓 1:1 |
| 代价 | 整体比参照高瘦（约束所致，非失误） | 抓取幅度变小，动画要重排 |

用户 2026-11-24 裁决：**走方案 2**。理由是原话"动画其实我只是要那种抖动和表现，其实也不用完全一样"。

---

## 1. 已决策（不要再翻案的部分）

1. **参照 = `ReferenceModel.blend`**（Tripo，43 mesh / 2,411 v / 2,929 tris / 100% 三角面 / 无骨架无动画 / 正面朝 −Y）。
2. **动画源 = `hero_animation_v14_p47_no_rail.blend`**（117 对象 / 93 网格 / 22,284 tris / 36 action，激活的 17 条全是 `*_V2` / 327 帧 @60fps）。只取节奏与结构，不取枢轴坐标。
3. **面数目标：≤3,000 tris**，"越低越好"。
4. **分步交付**：先模型（Stage-2 收口）、再动画（Stage-3）。Stage-2 完成前不写任何关键帧。
5. **单位 = 米，S=1**。不做整体缩放，所有件按参照实测坐标直接落位。

### 1.1 为什么不能等比放大（数据留档）

| 项 | 参照 | v14 | 比值 |
|---|---|---|---|
| 箱体宽 | 0.534 | 1.800 | 3.37× |
| 箱体深 | 0.434 | 1.560 | 3.59× |
| 箱体高 | 0.419 | 2.460 | 5.87× |
| 箱体高/宽 | **0.78** | **1.37** | — |
| 机械臂全长（肩→腕） | 0.28 | 3.00 | 10.7× |
| 臂长/箱宽 | **0.57** | **1.67** | — |

高宽比与臂身比都相反，不是同一台机器的不同尺度，**是两种设计**。任何"缩放后套动画"的做法都会让机械臂转 90° 时缩进机壳里（B′ 就是被这条约束逼成高瘦的）。

---

## 2. 两套坐标契约

### 2.1 参照契约（建模基准，已落 `reference/v4_rigspec.json`）

| 件 | 实测（米） |
|---|---|
| 箱体 | x −0.436..0.098 / y −0.203..0.231 / z 0.029..0.448 |
| 正面板 | x −0.283..0.054 / z 0.163..0.396 / 前凸 0.028 |
| 前横槽 | 0.2315 × 0.0121 × 0.0221 @ c(−0.1752, −0.2046, 0.097) |
| 料斗口沿 | z 0.589，r 0.176；颈部 z 0.462，r 0.070；中心 xy (−0.1183, 0.0022) |
| 颈环 | r 0.088，z 0.459..0.488 |
| 滑道 | x 0.002..0.496 / y −0.153..0.092 / z 0.047..0.143 |
| 滑道脚 | x ≈ 0.405，y = −0.1035 / +0.0425，pad r 0.032 @ z 0.008 |
| 箱体四脚 | (−0.383, −0.150) / (0.015, −0.150) / (−0.392, 0.160) / (0.018, 0.167)，r 0.0255 |
| 背面百叶 | x c −0.145，y 0.2051，z 0.1055..0.1935，7 片，间距 0.01467 |
| 机械臂关节 | base (−0.3647, −0.0524, 0.4454) · shldr (−0.418, −0.050, 0.615) · elbow (−0.226, −0.037, 0.725) · wrist (−0.163, −0.036, 0.706) · palm (−0.150, −0.034, 0.698) |

### 2.2 v14 动画契约（只取语义，坐标作废）

| 通道组 | v14 内容 | 迁移策略 |
|---|---|---|
| Yaw / Shoulder / Elbow / Wrist / Finger_L / Finger_R | **仅 `rotation_euler`**（6 对象，12 条活跃 F 曲线） | 尺度无关，**曲线形状可整条搬**，只换宿主对象 |
| Arm_Mount / Machine_Body / Machine_Hopper / Machine_OutputChute | 仅 `location` | 只保留机身微颤（f200 附近 y −0.012 量级），其余丢弃 |
| Machine_Root | `rotation_euler`（仅 f156.36–242.65） | 丢弃（参照没有整机旋转段） |
| Product | hide + location + scale（8 通道） | **必须重编**：旧路径 x 1.553 → 4.45，新滑道止于 x 0.496 |
| Idea | hide_render / hide_viewport / location / rotation（811 keys） | 待定（参照里没有这个件） |
| Machine_Light_01..03 / LightStrip | color + location | 保留语义，灯带改挂在 `Machine_LightStrip` |

---

## 3. Stage-1 已完成（体块与比例）

**产物**：`versions/rebuild_v7_s1.blend`（0.13 MB）
**渲染**：`renders/v7_s1/v7_{front,right,top,iso,armclose}.png`（workbench，material 色 + cavity，720 px）

| 项 | 参照 | v7 Stage-1 | 差 |
|---|---|---|---|
| tris | 2,929（全三角） | **2,352** | −20% |
| quads | 0 | **920** | — |
| ngon | 0 | 44（锥/柱端盖） | 待清零 |
| 对象数 | 43 散片 | **39** 命名件 | — |
| bbox x | −0.501..0.500 | −0.468..0.496 | −0.033 / −0.004 |
| bbox y | −0.231..0.231 | −0.235..0.231 | −0.004 / 0 |
| bbox z | 0..0.754 | 0..0.769 | **+0.015**（爪尖高 15 mm） |

**对象清单**（39）：`Machine_Body`、`Machine_WindowFrame`、`Machine_WindowGlass`、`Machine_FrontSlot`、`Machine_LightStrip`、`P3e_BackVent_0..4`、`P3d_TopDisc`、`Machine_Feet_0..3`、`Machine_Hopper`、`Machine_HopperNeck`、`P3d_HopperCollar`、`Machine_Chute`、`P1_OutletLip_L/R`、`Chute_Foot_0/1`、`Chute_Pad_0/1`、`Arm_Base`、`Arm_Riser`、`Arm_Shoulder_Joint`、`Arm_UpperArm`、`Arm_Elbow_Joint`、`Arm_Forearm`、`Arm_WristCollar`、`Arm_Gripper`、`Arm_Finger_{A,B,C}_s1/s2`。

**材质 6 个**：`M_Shell`(0.80,0.76,0.70, r0.38) · `M_ShellDk` · `M_Metal`(metal 0.85, r0.26) · `M_Rubber` · `M_Screen` · `M_Accent`(琥珀，emission 2.5)。

**v3 → v7 走过的弯路（别重犯）**

1. `primitive_cone_add` **默认封顶**——第一版料斗是个实心盘子，斜视图看得很清楚。改 bmesh 旋转：4 点剖面 × 20 段 = 80 quads，内壁单独材质，才有漏斗深度。
2. 臂杆半径 0.03 太细，像铁丝。参照的杆半径 ≈ 0.4 × 段长，是**短粗夹爪臂**。已加到 0.043–0.050。
3. 爪子按 Y 轴展开会让四指在前视图重叠成一根尖刺。**绕腕轴 120° 三指**才是任意角度都读得出的解。
4. 正面板做成"贴面的金属片"读不出凹。改成凸起边框 + 内凹深色屏。
5. `bm.to_mesh()` 之后 `BMFace` 引用失效——材质索引必须在 `to_mesh` **之前**写到 face 上。

---

## 4. Stage-2 待完成：细节 / 拓扑 / UV / 材质 / 导出

> 目标：tris ≤ 3,000，ngon = 0，quad ≥ 85%，GLB 回导 PASS。
> 全部在 `versions/rebuild_v8_s2.blend` 上做，**每项一个 pass，不覆盖**。

| # | 待办 | 做法 | 验收 |
|---|---|---|---|
| S2.1 | 背面散热栅是浮片，不是凹槽 | 5 片改成真凹：箱体背面布尔切槽 + 内衬片，或直接做 0.006 深的斜面凹槽 | `ref_right` / `v8_right` 对比，5 条缝在右视图可读出阴影；tris +≤120 |
| S2.2 | 滑道是光滑整板，缺侧壁与端口起伏 | 加 0.010 内壁 + 端帽倒角 + 近端支架小方块 | 正视/俯视轮廓与 `ref_front` / `ref_top` 的 IoU ≥ 0.97；tris +≤120 |
| S2.3 | 爪指偏瘦（现在 r 0.0135→0.005） | 加粗到根部 0.016，末节 0.007；顺带做 **120° 等分**（`exec/EXECUTION_PLAN.md` 老待办） | 三指根部角度误差 <1°；`v8_armclose` 与 `arm_front` 的指间距差 <0.006 |
| S2.4 | 正面板凹边是直角台阶 | 给内屏边框加 0.006 倒角（bevel 1 段） | iso 视图能读出 0.010 深的台阶；tris +≤40 |
| S2.5 | 44 个 ngon（锥/柱端盖） | 端盖改三角扇或 4 段四边面；导出前统一三角化校验一遍 | **ngons = 0**，quad ≥ 85%，tris ≤ 3,000 |
| S2.6 | 无 UV | 按材质边界拆 6 组，Smart UV Project（angle 66°, margin 0.02）+ 手工拉直外壳四条主边 | 0 重叠、0 反面；texel density 统一 512 px/m（±5%） |
| S2.7 | 材质是占位色 | 5 套 Principled PBR 定稿（壳 / 深壳 / 金属 / 橡胶 / 自发光），shell 走轻微 clearcoat | AgX 下渲一次正视，主体亮度落在 0.55–0.70；无过曝（§6 老坑：Standard 把奶油打到 #FFF） |
| S2.8 | 未导出 | 沿用 `scripts/export_glb.py`（**含 outliner 眼睛修复**，见 STATUS §10 第二坑） | `validate_glb_vis.py` PASS；GLB 回导 mesh 数 = 39、材质 6、无 NaN |

**Stage-2 出口判据**：`versions/rebuild_v8_s2.blend` + `export/hero_v3_s2.glb` + `renders/v8_s2/*` 五视图，全部数字写进 `STATUS.md` §11。

---

## 5. Stage-3 待完成：动画重编

> 前置：Stage-2 全部通过（几何与 UV 冻死之后才动关键帧）。
> 帧率/时长沿用 v14：**327 帧 @60 fps**。

### 5.1 枢轴链（新建 8 个 empty，父子传递）

```
Machine_Root
└─ Arm_Base            (−0.3647, −0.0524, 0.4454)   yaw
   └─ Arm_Riser_Pivot  (−0.3647, −0.0524, 0.4700)   pitch
      └─ Arm_Shoulder  (−0.4180, −0.0500, 0.6150)   pitch
         └─ Arm_Elbow  (−0.2260, −0.0370, 0.7250)   pitch
            └─ Arm_Wrist (−0.1630, −0.0360, 0.7060)
               ├─ Arm_Finger_A
               ├─ Arm_Finger_B
               ├─ Arm_Finger_C
               └─ Arm_GrabPoint  (爪尖中心，f1 实测)
```

网格件 `Arm_*` 全部 `parent` 到对应 empty，`matrix_parent_inverse` 保持单位阵以外的正确逆矩阵（**有父级的对象按世界坐标写 mesh 会静默位移**，见 STATUS §6）。

### 5.2 待办

| # | 待办 | 做法 | 验收 |
|---|---|---|---|
| S3.1 | 建枢轴链 | 上面那棵树，8 个 empty，分别记录 f1 世界坐标 | 8 个枢轴坐标与 §2.1 表逐位一致（±1e-4） |
| S3.2 | 搬 12 条旋转曲线 | 从 v14 `*_V2` action 取 Yaw/Shoulder/Elbow/Wrist/Finger_L/R 的 `rotation_euler` 曲线，按**归一化时间**重采样到新 action | 关节角曲线形状相关系数 ≥ 0.95；无 V14 残留对象 |
| S3.3 | 重编位移组 | 只保留机身微颤（振幅 ≤0.012 m，2 个倍频），丢弃 Mount/Hopper/Chute 的旧位移 | 机身位移 PSD 峰值 < 6 Hz，最大位移 ≤0.012 |
| S3.4 | 重编 Product 路径 | 新中心线：料斗口 → 滑道 → 出口 x 0.496。8 通道（hide + location + scale）全部重写 | f_first_visible 前 0 帧可见；x 单调递增；y 始终在 −0.153..0.092；**0 帧穿模**（BVH，世界空间树） |
| S3.5 | 灯带动画 | `Machine_LightStrip` 的 emission 强度呼吸 + 抓取成功时一次脉冲 | 峰值帧与抓取帧同步（±2 帧） |
| S3.6 | 整机循环 | 端点差归零 | `verify_anim` 口径 loop 差 = 0.0 |
| S3.7 | 语义门禁（**新写**） | 枢轴全变了，旧的 `verify_anim.py` 世界矩阵比对**不再适用**。新写 `qa_v3/stage3_gate.py` | f_grab 爪尖落在斗口上方 ±0.06；f_drop 爪尖进斗口 r 内；Product 出口段速度单调；0 穿模 |

### 5.3 为什么必须新写门禁

`scripts/verify_anim.py` 是拿 p19 的世界矩阵逐点比对的（136 点，阈值 1e-4）。这套尺子只对"原地换 mesh"（B′）有效。方案 2 的枢轴坐标全换，任何世界矩阵比对都会 100% 失败——**不是 bug，是尺子不对**。新门禁要判语义：爪尖到斗口的距离、Product 的中心线单调性、穿模帧数。

---

## 6. Stage-4 交付

| # | 待办 | 验收 |
|---|---|---|
| S4.1 | GLB（`use_visible=True`，烘焙 hide 通道为 scale） | 回导 mesh/材质/动画数与 blend 一致 |
| S4.2 | FBX（`apply_scale=True`, `bake_anim=True`） | 回导无警告 |
| S4.3 | 动画 QA | 抽 12 帧出 contact sheet，跑 `animation-quality-gate`：轮廓稳定、无闪烁、主体占比 >35% |
| S4.4 | 文档收口 | `STATUS.md` §11 完整账 + `BUILD_NOTES.md` 补一节 |

---

## 7. 依赖与顺序

```
Stage-2 ──┬─ S2.1..S2.5（几何，可并行）
          ├─ S2.6 UV        ← 必须在 S2.5 之后（拓扑改了 UV 就废）
          ├─ S2.7 材质      ← 依赖 UV
          └─ S2.8 导出      ← 依赖前面全部
Stage-3 ── S3.1 ← Stage-2 冻结
          S3.2..S3.6（曲线，可并行） ← 依赖 S3.1
          S3.7 ← 依赖全部
Stage-4 ── 依赖 Stage-3
```

**不要跳步**：S2.6 之后如果又改拓扑，UV 必须重做；S3.1 之后如果又动枢轴坐标，S3.2 的曲线要重采样。

---

## 8. 风险与已知取舍

| 风险 | 影响 | 对策 |
|---|---|---|
| 参照的臂太短（肩→腕 0.28 m） | 抓取幅度只有 v14 的 1/10，"表演"会被压缩 | 靠相机推近 + 机身微颤 + 灯带脉冲补；必要时允许肘部超量 15% |
| 滑道是闭合管，不是 v14 那种开放 U 槽 | Product 出口语义要重定义 | 端帽做成开口 + 内壁，Product 从端口滑出；不做贯穿开孔（会破轮廓） |
| 44 个 ngon 来自锥/柱端盖 | 导出三角化后可能出现细长三角 | S2.5 统一处理成三角扇，导出前校验最小面积 > 1e-8 |
| 参照的 2 个占位材质无信息 | 配色无据可依 | 沿用 v13/v14 的奶油壳 + 琥珀强调，Stage-2 用 AgX 校准 |
| 爪尖 z 高 15 mm（0.769 vs 0.754） | 整体轮廓略超 | S2.3 加粗手指时顺手收回 0.015 |
| `Action.fcurves` 在 5.x 已移除 | 取曲线会直接 AttributeError | 走 `action.layers → strips → channelbags → cbag.fcurves`；重挂 action 必须同时匹配 `animation_data.action_slot`，否则对象完全不动 |

---

## 9. 复现

```powershell
# Stage-1 基线（v7）：本计划 §3 的全部数字
# 视角/灯光口径见本轮脚本：workbench / STUDIO / MATERIAL 色 / cavity BOTH / AA 16 / ortho_scale 1.15 / center (−0.0005, 0, 0.377)
& "G:\Blender\blender-5.3.0\blender.exe" --background --factory-startup --python <stage1.py>

# Stage-1 渲染（五视图）
& "G:\Blender\blender-5.3.0\blender.exe" --background --factory-startup --python <views.py>

# 统计口径
#   tris  = sum(len(p.vertices) - 2 for p in mesh.polygons)
#   quads = sum(1 for p in mesh.polygons if len(p.vertices) == 4)
#   bbox  = matrix_world @ bound_box，逐对象取并集
```

Blender：`G:\Blender\blender-5.3.0\blender.exe`（建模/渲染，稳定）。`5.4.0-alpha` 只用于 MCP 现场演示。
dsh-blender 插件的 `blender_*` 工具在本机 **ENOENT**（`spawn blender ENOENT`，未上 PATH），一律走 `--background`。

---

## 10. 与旧台账的关系

- `STATUS.md` §10 的路线 B′ **不废弃**：它是一份可用的、动画零风险的重建（16,050 tris / 92% 四边面 / `export/hero_v2.glb`）。本计划是**并列的第二方案**，交付物命名带 `v3` 前缀（`rebuild_v*_s*`、`hero_v3_s2.glb`）以免混淆。
- `exec/EXECUTION_PLAN.md` 里未完成的"爪 120° 等分""底座碗形内收弧"并入本计划 S2.3 / S2.4。
- 沉孔可见性 12/20（STATUS §8-2）**不在本计划范围内**：参照模型没有那 20 颗沉孔螺钉，方案 2 不继承这套特征。
