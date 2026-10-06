# AGENTS.md — 本项目（Blender 头像实验）工作约定

> 本文件是**项目级**约定，补充而**不覆盖**全局 OMX `AGENTS.md`（编排 / 技能路由 / 团队流程以全局为准）。

## 项目目标

用 Blender + MCP 把照片 / 参考图做成**能被浏览器摄像头驱动的 3D 头像**。
链路：MediaPipe FaceLandmarker -> ARKit 52 blendshape -> three.js morph target（库名 aniface）。

## 环境

| 项 | 值 |
|---|---|
| 平台 | Windows，PowerShell |
| Blender | 5.2.2 LTS，安装在 `C:\Program Files\Blender Foundation\Blender 5.2` |
| MCP | `mcp-for-blender`（插件在 Blender 用户目录；Codex 中服务名为 `blender`） |
| uv / uvx | miniconda 下：`<HOME>\miniconda3\Scripts\uvx.exe` |
| 摄像头 | **本机没有摄像头**；实时驱动需另一台机器 + https |
| 演示工程 | `aniface-demo/`，`npm run dev` -> https://localhost:5199/ |

## 与 Blender 交互的约定

- 优先用 `execute_blender_code` 跑脚本；**长脚本先写成 .py 文件再 `exec(open(...).read())`**，便于迭代与复用。
- `look` 的场景预览**可能返回缓存图**。可靠验证方式：先 `bpy.ops.render.render(write_still=True)` 渲染到文件，再 `look(image=<path>)`。
- 改完几何要 `me.update()` + `bpy.context.view_layer.update()`；读边界盒用 `evaluated_get(depsgraph)`。

## 血泪教训（务必遵守）

### Blender 网格

1. **有 shape key 的网格，改 `mesh.vertices[].co` 对渲染无效** —— 必须改**每一个 shape key 块**（`shape_keys.key_blocks[*].data`）。
2. 某些模型上 **`mesh.vertices` 与 `Basis` 块不是同一份数据**：读顶点位置要用 `shape_keys.key_blocks["Basis"].data`。
3. **glTF 导入后局部坐标常是 OBJ 原样（Y-up）**，靠对象旋转变成世界 Z-up。做投影 / 拟合前先用已知特征（眼睛、牙齿）确认轴向。
4. 进编辑模式删几何前，**必须先在编辑模式内 `select_all(action='DESELECT')`**，否则会因顶点全选而**清空整个网格**。
5. 法线可能不一致 -> 用 `mesh.normals_make_consistent(inside=False)` 重算（本例修复后贴图覆盖面 1894 -> 7882 面）。
6. **`0 * NaN = NaN`**：用位置图做逻辑运算前先 `np.nan_to_num`，否则 NaN 会污染平滑 / 遮罩并被渲染成黑色。
7. 位置图要用**三角形光栅化**（逐三角形重心插值），不要用 Voronoi 最近邻——后者边界粗糙，绘制结果全是锯齿。

### glTF 导出（给 aniface）

8. **禁用 Draco**（aniface 的 GLTFLoader 没配 DRACOLoader，加载会失败）。
9. **meshopt 压缩可用且推荐**（`Avatar.ts` 里设了 `MeshoptDecoder`）。
10. 用 `export_morph_normal=False`（省一半 morph 数据）、`export_yup=True`、`export_skins=False`（头模型）。
11. 体积主要由 **morph targets** 决定。三招瘦身：删无用几何、关 morph 法线、开 meshopt。（本例 97.7 MB -> 0.84 MB）

### ARKit 表情命名

12. aniface **按名字精确匹配**（大小写敏感）。ICT-FaceKit 用 `eyeBlink_L/_R` -> 要改成 `eyeBlinkLeft/Right`；`browInnerUp_L/_R` 与 `cheekPuff_L/_R` 需**合并成一个**（delta 相加）。
13. 缺 `tongueOut` 可接受（aniface 会跳过）。小熊猫基座（raccoon）**52 个全有**，人类头缺 `tongueOut`。

### aniface

14. **head-only 分支每帧覆盖 `gltf.scene.matrix`** -> 想调整位置 / 缩放必须**外套一个 `THREE.Group`**，改 wrapper 的 transform。
15. `modelOptions.autoRotate` 默认 `true` 且 `rotation = Math.PI`，会把模型转 180 度 -> 必须显式 `autoRotate: false, rotation: 0`。
16. 贴图采样用**当前 active_render 的 UV 层**；切到投影 UV 后要记得切回 `UVMap`，否则贴图全乱。

### 贴图 / 投影

17. **不要把带表情的照片平面投影到模型上**：会把舌头、张口、光照**烤进中性表情**，且球面投影会把眼周拉变形。做中性基座请用**贴图配色重映射**。
18. 本项目基座贴图（raccoon）**脸岛仅约 100x140 像素**，且**左右镜像共用 UV**（对称绘制方便，但精细斑纹画不出来）。要手工画斑纹必须先**重新展 UV 并提高分辨率**。

### 网络 / 运行环境

19. `getUserMedia` 只在 **https 或 http://localhost** 下存在；用局域网 IP + http 会得到 `Cannot read properties of undefined (reading 'getUserMedia')`。演示页顶部有 `origin / secure / mediaDevices` 自检行。
20. 用 `https://` 访问**只讲 HTTP 的服务**会报 `ERR_SSL_PROTOCOL_ERROR`。`aniface-demo` 默认已启用 HTTPS（`certs/` 存在即生效）。
21. `selfsigned` **v5 是 async-only**（要 `await generate(...)`）；证书需带 SAN（含本机 IP），否则浏览器报名称不匹配。

## 验证清单（改动后必做）

```powershell
# 1) GLB 规格
uv run --python 3.11 --with numpy python glb_verify.py
#    期望：morph 名 52/52 ARKit；extensionsRequired = EXT_meshopt_compression；
#          skins = 0（head-only）；无 draco
# 2) 渲染对比：Blender 内渲染到文件后 look(image=...)
# 3) 静态服务：https://<本机IP>:5199/ 与 /redpanda_head.glb 均返回 200
```

## 不要做的事

- 不要用 `Start-Process` 起后台 npm 服务（本机策略会拒绝）；用前台 `exec_command` 起会话。
- 5173 端口属于另一个项目，不要占用或终止其进程。
- 不要把 `certs/`（私钥）、`*.npy`（派生数据）、`node_modules/`、`ICT-FaceKit/` 提交进 git。
