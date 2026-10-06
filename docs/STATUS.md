# 项目状态：Blender 头像实验

更新日期：2026-10-06

## 一、目标与链路

用 Blender + MCP 把照片 / 参考图做成**浏览器摄像头可驱动的 3D 头像**。

链路：摄像头 → MediaPipe FaceLandmarker → ARKit 52 blendshape → three.js morph target（库：aniface，模型：GLB）。

关键约束：**模型必须带 ARKit 命名的 morph target**（按名字精确匹配、大小写敏感），否则 aniface 只做头部旋转、脸是死的。

## 二、已完成的两条流水线

### 流水线 A：真人照片 → 人头（ICT-FaceKit）

1. clone `USC-ICT/ICT-FaceKit`（MIT）：26,719 顶点，53 个 ARKit 命名 shape key，UV 齐全
2. 装载：`wm.obj_import` 逐个导入 + `join_shapes` → 54 个 shape key（Basis + 53）
3. MediaPipe 468 关键点 → 29 个语义对应点（画图人工校验对应关系）
4. 身份拟合：60 个 PCA 模式 + 相似变换，交替最小二乘 + 岭回归。结果 |c|=3.0，重投影 RMSE 22.9px（约脸宽 5%）
5. 把合成增量写进全部 shape key 块，统一缩放居中（头高 0.26 m）
6. 法线重算朝外（贴图覆盖面 1894 → 7882 面）
7. 照片平面投影到正脸 + 眼周材质透明化
8. shape key 重命名：`_L`→`Left`、`_R`→`Right`；合并 `browInnerUp` / `cheekPuff` → 51 个精确 ARKit 名（缺 `tongueOut`）
9. 瘦身导出：删眼球/牙齿/牙龈/睫毛（26,719 → 14,062 顶点）+ 关 morph 法线 + meshopt → 97.7 MB → 20.2 MB

产物：`aniface_head.glb`（20 MB，51 表情）、`pipeline.py`、`fit3.py`、`mp_lm.py`、`ict_fit.json`

### 流水线 B：小熊猫（基于 raccoon 基座）

1. 用 aniface 官方 demo 素材 `raccoon_head_small.glb` 作基座（MIT；自带 52 个 ARKit 表情，含 `tongueOut`）
2. 配色重映射：按亮度分区把原贴图改成小熊猫色板 —— 深→深红棕（眼罩/鼻）、中→锈橘（主体）、浅→奶白（吻/耳缘）
3. 耳朵单独一套贴图：白边 + 橘心
4. 修正 UV 层（曾误用投影 UV 导致贴图错乱）
5. 导出：meshopt + 关 morph 法线 → 1.37 MB → 0.84 MB
6. 手工斑纹尝试：按 3D 坐标绘制白眉弧 / 额中白纹 / 白颊（受 UV 分辨率限制，效果很淡）

产物：`redpanda_head.glb`（0.84 MB，52 表情）、`redpanda_base3.png`、`redpanda_ear3.png`

## 三、当前问题清单

### 已解决

| 问题 | 根因 | 解决 |
|---|---|---|
| 调不了位置 / 缩放 | aniface head-only 每帧覆盖 `gltf.scene.matrix` | 外套 `THREE.Group`，改 wrapper |
| 模型崩坏（眼睛错位、舌头常在） | 把带吐舌头的照片平面投影，表情/光照被烤进中性脸 | 撤掉照片投影，改用贴图配色重映射 |
| 侧面出现青蓝色块 | 头部 UV 落在图集的「衣服」区域，重映射时保留了饱和色 | 改为全图重映射 |
| 眼周黑色放射杂点 | 眼区 UV 三角形极密，3D 坐标绘制权重剧烈跳变 | 排除眼区不绘制 |
| 中间一条黑虚线 | 位置图未覆盖 texel 为 NaN，`0 * NaN = NaN` 污染平滑 | `np.nan_to_num` + 显式 mask 归零 |
| 接缝孤立斑点 | 镜像 UV 接缝处权重断续 | 形态学开运算（腐蚀 + 膨胀） |
| 跨机器摄像头报 `getUserMedia` undefined | 非安全上下文（局域网 IP + http） | 演示工程默认启用 HTTPS + SAN 证书 |
| 远端 `ERR_SSL_PROTOCOL_ERROR` | 用 https 访问了 HTTP 模式的服务 | 配置改为 `certs/` 存在即默认 HTTPS |

### 未解决 / 待改进

| # | 问题 | 严重度 | 说明与可能路径 |
|---|---|---|---|
| 1 | **小熊猫精细斑纹做不出来** | 高 | 基座贴图**脸岛仅约 100x140 px**，且左右镜像共用 UV，按 3D 坐标绘制分辨率不够。正确路径：**重新展 UV（Smart UV Project / 手工接缝）+ 提到 1K~2K，烘焙现有颜色后再手工绘制** |
| 2 | 耳朵是侧向的（继承 raccoon） | 中 | 真正小熊猫是直立耳。需旋转 `ears_geo` 并同步调整头顶蒙皮 |
| 3 | 人类头像脸型偏窄长 | 中 | 仅 29 个 2D 约束、无深度约束，线性模型也拟合不到 100%。可增加对应点或加入 3D 旋转 |
| 4 | 人类头缺 `tongueOut` | 低 | 可用 `mapBlendshapeNames` 从别处补，或手工雕一个 shape key |
| 5 | 无身体、无耳朵/尾巴骨骼 | 低 | aniface 只管脸 + 头旋转；耳朵/尾巴动需自己写骨骼驱动 |
| 6 | 本机无摄像头，实时链路未端到端验证 | 中 | 需在另一台机器 https 打开；或先用文件模式 + 手动滑块验证模型侧 |

## 四、交付物

| 文件 | 说明 |
|---|---|
| `aniface-demo/` | 可运行演示：摄像头 / 文件 / 手动滑块三种驱动 + 位置缩放控制 + HTTPS |
| `aniface-demo/public/redpanda_head.glb` | 小熊猫头像，52 ARKit 表情，0.84 MB |
| `aniface_head.glb` | 人类头像，51 ARKit 表情，20 MB |
| `pipeline.py` | 人类头像一键重建 |
| `fit3.py` + `mp_lm.py` | MediaPipe 关键点 → ICT 身份系数拟合 |
| `rp_*.py` / `paint_uv*.py` | 小熊猫制作与贴图绘制脚本 |
| `glb_verify.py` | GLB 规格校验（morph 名 / 扩展 / skin） |
| `AGENTS.md` | 项目级工作约定与踩坑清单 |

## 五、下一步建议（按性价比）

1. **重新展 UV + 提升贴图分辨率**（解决问题 1，收益最大）：Smart UV Project / 手工接缝 → 1K~2K；先把当前颜色烘焙到新 UV，再手工绘制白眉斑、额中白纹、白颊、耳缘
2. **耳朵立起来**（问题 2，视觉提升明显）
3. **端到端实时验证**（问题 6）：在有摄像头的机器上 `npm run cert && npm run dev`
4. 人类头脸型拟合增强（问题 3）：补关键点 + 加 3D 旋转

## 六、常用命令

```
cd aniface-demo; npm run dev            # https://localhost:5199/
npm run cert                            # 本机 IP 变化后重签证书
uv run --python 3.11 --with numpy python glb_verify.py
uv run --python 3.11 --with "mediapipe==0.10.14" --with pillow --with numpy python mp_lm.py
uv run --python 3.11 --with numpy python fit3.py
```
