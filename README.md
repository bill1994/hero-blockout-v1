# Hero Blockout V1 —— 商业网站 Hero 区 4 秒循环白模动画

60fps / 240 帧 / 4 秒无缝循环。左臂抓取 Idea 球 → 顶部漏斗 → 加工反应 →
右侧出料 → 复位。集合 `HERO_BLOCKOUT_V01`，灰阶白模，机位 `Cam_Hero` 锁定。

- 当前版本：`hero_blockout_v01_final_v7.blend`（纯白模：灯 / 材质 / 灯光冻结）
- 60fps 基线：`hero_blockout_v01_final_v5.blend`（复位缓入缓出，无停顿）
- 加工反应执行提示词见 `processing_reaction_prompt.md`（本仓库未收录，本地同目录有）。
- 各阶段逐帧数值与管线教训写在 blend 内嵌文本 `HERO_SPEC` / `ARM_POSES` 里。

## 打开方式

Blender 5.1+ 直接打开即可（动画数据全在文件里，不依赖任何插件）。
如需复现 DSH 直连操作，需另装官方 Blender Lab MCP 扩展（Host `localhost` / Port `9876`）。
