# P18 审查报告 — hero_animation_v14_p18.blend

**审查时间**：2026-11-03
**对象**：`hero_animation_v14_p18.blend`（873,741 B，2026-11-03 10:20）
**工具**：Blender 5.4.0 Alpha（`G:\Blender\blender-5.4.0-alpha\blender.exe`）后台模式 + 官方 Blender MCP（`blender-mcp 1.30.0`，26 工具）
**审查方式**：全部为实测（raycast / depsgraph 求值 / 逐帧渲染），非文档推断

---

## 一、总评

**画面与动画质量已接近可交付，但存在 3 个必须修的硬问题，其中 1 个是 P18 引入的性能回归。**

| 维度 | 评价 |
|---|---|
| 造型与材质 | 优秀。奶白/薄荷/琥珀/炭灰四色分区清晰，等离子窗口、倒角纪律、螺丝头、玻璃材质都在位，不是 blockout 水平 |
| 动画逻辑 | 优秀。抓取→搬运→落料→出料→归位，故事线完整可读 |
| 关键指标 | 优秀。抓取距离、循环闭合均与 STATUS 记录完全一致 |
| 性能预算 | **超标 12.4%**，P18 回归 |
| 装配关系 | **产品悬空 0.18–0.19**，破坏 P6 契约 |
| 交付完整性 | **缺 GLB、缺文档记录** |

---

## 二、三个必修问题

### 🔴 P1 三角面超预算 112.4%（P18 引入的回归）

| 版本 | 三角面 | 占 60k 预算 |
|---|---|---|
| v14 P4 | 25,712 | 42.9% |
| v14 P6 | 29,134 | 48.6% |
| v14 P7 | 26,612 | 44.4% |
| **v14 P18** | **67,444** | **112.4%** |

**根因**：P18 给 `Machine_Chute` 和 `P1_ChuteSeat` 各加了一个 `Smooth_Outlet` SUBSURF 修改器，`render_levels = 2`。P7 时这两个对象只有 `Smooth by Angle`（NODES），没有 SUBSURF。

实测各级别面数：

| 对象 | 基础面 | L0 | L1 | L2（现状） |
|---|---|---|---|---|
| Machine_Chute | 750 | 1,400 | 5,800 | 23,200 |
| P1_ChuteSeat | 650 | 1,200 | 5,000 | 20,000 |
| **全场** | | 26,844 (44.7%) | **35,044 (58.4%)** | 67,444 (112.4%) |

**建议**：`Smooth_Outlet.render_levels` 由 2 改为 1 → 全场降至 35,044 面（58.4%），回到预算内且仍保留平滑效果。若视觉上 L1 足够，这是最小改动方案。

### 🔴 P2 产品悬空，破坏 P6 出料槽契约

P6 在 STATUS 中明确定义了契约：`trough floor 1.085`，且「Product still seats at f232 with a 0.001 gap over the trough floor 1.085」。

**P18 实测（射线投射，从产品底面下方向上打）**：

| 帧 | 产品底 z | 命中槽底 z | 间隙 |
|---|---|---|---|
| f240 | 1.0935 | 0.9108 (P1_ChuteSeat) | **0.183** |
| f245 | 1.0860 | 0.9002 (P1_ChuteSeat) | **0.186** |
| f255 | 1.0860 | 0.8945 (P1_ChuteSeat) | **0.192** |
| f280 | 1.0860 | 0.8897 (P1_ChuteSeat) | **0.196** |

**问题**：P18 的出料槽槽底已下沉到约 0.89–0.91（P6 契约是 1.085），但 `Product` 的动画仍按旧的 1.085 高度走。**两者没同步更新**，导致产品悬空 0.18–0.19（约 2cm 视觉尺度），侧视图 `side_f245.png` 可见明显的黑色缝隙。

同时 `Machine_Chute` bbox z 最低到 0.968，而 P6 契约是槽底 1.085 / 外底 1.035。

**建议**：把 `ProductAction.001_V2` 的 location[2] 关键帧整体下移约 0.19（配合 P18 实际的槽底高度），或把出料槽几何抬回契约高度。二者必须对齐其一。

### 🟡 P3 产品在 f265–f280 有明显悬空抬升

| 帧 | 产品 z 范围 | 说明 |
|---|---|---|
| f260 | 1.4196–2.3269 | 底部抬到 1.42，比槽底高 0.53 |
| f265 | 1.3961–2.3523 | 悬空抬升 |
| f280 | 1.0860–2.0832 | 底部回到 1.086，但顶部 2.08（产品被拉长） |

f260–f280 段产品同时出现「抬高 + 纵向拉伸」，配合 scale 动画（0.7 → 变化中），视觉上像是产品在槽上方弹跳/变形。f250 单帧看是正常的白方块，但连续播放这段会露馅。

---

## 三、已验证通过的项

### 抓取距离（对齐 STATUS 记录）
球半径 0.25，接触距离应约 0.25：

| 帧 | Finger_L | Finger_R | Finger_C |
|---|---|---|---|
| f31 | 0.2531 | 0.2560 | 0.2526 |
| f43 | 0.2531 | 0.2560 | 0.2526 |
| f96 | 0.2531 | 0.2560 | 0.2526 |
| f147 | 0.2677 | 0.2703 | 0.2526 |

与 STATUS.md 记载的「f31/43 → 0.2531/0.2560，f147 → 0.2677/0.2703」**逐位一致**。

### 循环闭合
f1 与 f327 全部 MESH/EMPTY 对象位置差异：**0 个**（完美闭合）。

### 动画时序
- 帧范围 1–327 @ 60fps = **5.45 秒**
- `Idea`（琥珀球）可见性：f1–155 可见 → f156.4 隐藏 → f310.4 隐藏 → f311.5 可见
- `Product` 可见性：f1–230.9 隐藏 → f231.7 可见 → f326.5 隐藏
- 关键节拍：抓取 f2–39 / 搬运 f48–156 / 落料 f156 / 产品生成 f232–240 / 滑出 f240–301 / 复位 f301–311
- 全部 17 个受控对象均使用 V2 action，slot 绑定全部正确（`slot_in_use ∈ slots`）

### 数据卫生
- 孤立网格 / 材质 / 贴图：**均为 0**
- 渲染引擎 EEVEE，32 采样，1100×1100，view transform Standard，exposure 0
- 三点布光 + 双 SUN 完整

---

## 四、其他发现（非阻塞）

### 1. `scene.camera = None`
场景**没有设置活动相机**。三台相机（`Cam_Hero` 透视 45.7mm / `Cam_Check_Right` 正交 / `Cam_Check_Top` 正交）都在 `Camera` 集合里，但 `scene.camera` 为空。直接 F12 渲染会报错或用默认视角。**导出 GLB 前必须显式指定相机**。

### 2. 19 个闲置 action（36 个中过半未使用）
所有 V1 action 已被 V2 全面接管，但 V1 仍保留在文件里未清理：
`Arm_*Action`（7个）、`Machine_*Action`（8个）、`IdeaAction`、`ProductAction.001`、`Machine_WindowAction`、`Machine_WindowAction_V2`（空 action，0 曲线）。

其中 `Machine_WindowAction_V2` 是**完全空 action**（0 条 fcurve），对应的 `Machine_Window` 对象**在 P18 中已不存在**（只剩 `Machine_WindowCavity/Frame/Glass/Glow` 零件）。建议清理以减小文件体积、避免误导。

### 3. 尾部静止
`Machine_Hopper`、`Machine_Body`、`Machine_OutputChute`、`Arm_Shoulder_Pivot` 的动作在 f243 结束，到 f327 有 **84 帧（1.4 秒）静止**。若这是刻意的「停顿收尾」则没问题；若期望是循环动画，尾部偏长。参考 STATUS 中记录的 loop delta 为 0.000，说明循环是设计过的。

### 4. `Machine_Root` 的 motion segment 显示为空
`Machine_RootAction_V2` 驱动的是 `rotation_euler`（不是 location），所以位置轨迹全零是正常的——它是旋转抖动，不是位移。

### 5. 集合归属小瑕疵
- `Arm_WristCollar` 单独落在 `Collection` 里，语义上应属 `Arm`
- `HERO_BLOCKOUT_V01` 集合本身为空（objects=0），只作为父级挂着 Arm/Camera/Machine/Props
- `LEGACY_UNUSED` 装着 `Prop_IdeaPedestal`（已隐藏）

---

## 五、交付缺口

| 项 | 状态 |
|---|---|
| `hero_animation_v14_p18.glb` | **不存在**（P4/P6 有，P5/P7/P18 都没有） |
| STATUS.md 中的 P18 条目 | **不存在**（文档只记录到 P6） |
| BUILD_NOTES.md 中的 P18 条目 | **不存在** |
| `validation/v14_gap/` | 目录存在（11-03 10:20），但需确认内容是否为 P18 产出 |

**导出 GLB 前的检查清单**：
1. 先修 P1（SUBSURF 降到 L1），否则 GLB 会带着 67k 面导出
2. 先修 P2（产品与槽底对齐）
3. 显式设置 `scene.camera = Cam_Hero`
4. 导出时用 `use_visible=True`（`Machine_Light_01/02/03`、`Machine_LightStrip`、`Arm_Mount`、`Product_Proxy_*` 等是刻意隐藏的）
5. 记得 `MAT_Nebula_Plasma_Baked` 是烘焙贴图（`plasma_bake.png` 已 packed），程序化节点不会进 glTF

---

## 六、审查产物

`review/p18_audit/` 目录：

| 文件 | 内容 |
|---|---|
| `p18_contact_sheet.png` | 8 帧动画弧线拼图（f1/f60/f120/f160/f200/f250/f300/f327） |
| `side_f245.png` | 正交侧视 —— 产品悬空证据 |
| `side_f265.png` | 正交侧视 —— f265 抬升段 |
| `p18_report.json` | 数据块总览、对象清单、几何统计、材质贴图 |
| `p18_anim.json` | 逐对象 fcurve 明细：关键帧数、通道、插值方式、时序覆盖 |
| `p18_paths.json` | 全部 36 个 action 的 data_path / 关键帧区间 |
| `p18_logic.json` | 抓取距离、落球轨迹、可见性关键帧、循环闭合差异 |
| `p18_final.json` | 三角面预算、孤立数据、集合归属、装配间隙 |
