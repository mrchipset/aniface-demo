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

### aniface 运行时（demo 开发中实测）

22. **head-only 分支会把矩阵放大 40 倍**：`AvatarRenderer.processLandmarks` 里
    `const scale = avatar.isFullBodyAvatar() ? 1 : 40`，`Avatar.applyMatrix` 会把这个 40
    乘进矩阵 3x3 -> 模型实际大 40 倍。**必须抵消**：
    `decompose` 内层矩阵读实际缩放 `s`，再设 `wrapper.scale = 用户Scale / s`。
    否则用户要先把 Scale 调到 ~0.025 才看得见，表现为「只能看到一张大嘴」。
23. **head-only 分支内部已经镜像过 Y/Z**（源码里写着 `const y = -this._tempEuler.y`）。
    做画面合成时若再翻一次，会**双重镜像**、动作反了。
    正确规则：`pasteMirror = !viewMirror`。
24. **head-only 分支会把人脸矩阵的平移分量写进模型根节点**
    （`matrix.decompose(position,...)` -> `compose`），模型会在画布内跑偏。
    修法是**直接清零 `matrix.elements[12..14]`**（尺度无关）；
    ⚠️ 不要用 `wrapper.position - p * scale` 去抵消 —— 人脸矩阵平移的量级与模型空间不一致，
    会把模型推到相机跟前（表现为全黑）。
25. **清零平移必须在 `render()` 之前**。`Aniface.processLandmarkData()` 内部已经渲染过一次，
    所以要用公开方法自己编排：`renderer.processLandmarks(r)` -> 清平移 -> `renderer.render()`。
26. **不要把 `OrbitControls` 的滚轮缩放留给用户当默认**（很容易误触把人贴到模型脸上）。
    给一个「重置视图」按钮，把相机拉回默认 `position/fov/lookAt`。

### 前端 canvas 合成

27. **2D 绘制的每个分支都必须自己 `translate`**：写
    `if (A) { ctx.translate(dx,dy); draw() } else { draw() }` 会让 else 分支永远画在 (0,0)。
    本项目的「合成偏移滑块无效 + 模型固定在左上角」就是这条引起的。**分支要对称**。
28. 合成画布的尺寸要按**源的固有尺寸**设置（`video.videoWidth/Height`、`img.naturalWidth`），
    再用 CSS 缩放显示；否则人脸框坐标（归一化）换算会错。
29. **删掉/改名 HTML 元素后，脚本里的 `$('id')` 会变 null** 并抛
    `Cannot set properties of null`。改完布局务必跑 `npm run check`（见 aniface-demo）。

### 调试方法（本次最有效的两条）

30. **把关键中间值直接显示在页面上**（如 `模型内层缩放 / 相机位置 / 贴图矩形 / 滑块值`），
    比"用户描述 -> 我猜 -> 改代码 -> 再问"快得多。不知道哪一环出问题时，先加可见数值。
31. 别在"我以为"的基础上连做两次修复（本项目「镜像坐标」那次是错的，
    真因是 else 分支漏 translate）。**先确认现象是"没生效"还是"方向反了"**，两者修法相反。
32. **延迟初始化的循环依赖是隐蔽杀手**：`updateMaskCanvas` 需要 `maskCanvas`，
    而 `maskCanvas` 只在 `ensureOffscreens` 里建，`ensureOffscreens` 又只在
    `drawVideoLayer` 的"已启用"分支里调用 —— 于是"没遮罩 → 不初始化 → 拿不到画布 → 没遮罩"，
    异常还被 try/catch 吞掉，表现为"怎么调参数都没反应"。
    **规则**：任何函数都应能独立保证自己依赖的对象存在；初始化不要挂在"功能已生效"的分支里。
33. **留一条可见的状态/诊断输出**：这类死锁只看现象无法定位，
    把「状态/是否有遮罩/类型/占比/参数」显示在页面上，一眼就能看出断在哪一环。
34. MediaPipe `ImageSegmenter` 的输出不统一：`selfie_segmenter` 多数版本只给
    `categoryMask`（0/1，`getAsUint8Array`），部分版本给 `confidenceMasks`（0..1，
    `getAsFloat32Array`）。**两种都要兼容**；遮罩极性不确定时给一个「反转遮罩」开关兜底。

### 贴图 / 投影

17. **不要把带表情的照片平面投影到模型上**：会把舌头、张口、光照**烤进中性表情**，且球面投影会把眼周拉变形。做中性基座请用**贴图配色重映射**。
18. 本项目基座贴图（raccoon）**脸岛仅约 100x140 像素**，且**左右镜像共用 UV**（对称绘制方便，但精细斑纹画不出来）。要手工画斑纹必须先**重新展 UV 并提高分辨率**。

### 网络 / 运行环境

19. `getUserMedia` 只在 **https 或 http://localhost** 下存在；用局域网 IP + http 会得到 `Cannot read properties of undefined (reading 'getUserMedia')`。演示页顶部有 `origin / secure / mediaDevices` 自检行。
20. 用 `https://` 访问**只讲 HTTP 的服务**会报 `ERR_SSL_PROTOCOL_ERROR`。`aniface-demo` 默认已启用 HTTPS（`certs/` 存在即生效）。
21. `selfsigned` **v5 是 async-only**（要 `await generate(...)`）；证书需带 SAN（含本机 IP），否则浏览器报名称不匹配。
22. **部署到子路径（GitHub Pages 的 `/<repo>/`）时，静态资源的根绝对路径会 404**。`main.js` 里所有资源路径必须走 `asset()`（= `import.meta.env.BASE_URL` + 相对路径），构建时用 `BASE_PATH=/<repo>/ npm run build`。新增资源别写 `/xxx`。
23. GitHub Pages 只发布 **Actions artifact**，所以 `public/mediapipe/`（36MB）不入库也可用——CI 里跑 `npm run vendor:mediapipe` 现生成（WASM 取自 `node_modules`，模型从 Google 官方下载）。仓库根是 `blender/`，工作流里 `working-directory: aniface-demo`、`path: aniface-demo/dist`，别搞错层级。
24. **建模产物与脚本一律放 `work/` 下**，仓库根只保留文档与 `aniface-demo/`。`work/assets/` 保持**扁平**是刻意的：历史脚本用裸文件名读写素材，路径相对**进程 CWD**，拆子目录会让 60 多个脚本一起失效；只有确定没脚本读取的渲染图才进 `work/assets/renders/`。`.blend` 用 `//` 相对路径引用贴图，**必须和贴图同目录**。
25. 跑主线脚本用 `work/scripts/pipeline.py`（自带路径自定位，从任意目录都能找到 `work/assets`）；跑 `redpanda/` 下的历史脚本前先把 CWD 切到 `work/assets`。

## 验证清单（改动后必做）

```powershell
# 1) GLB 规格
uv run --python 3.11 --with numpy python work\scripts\tools\glb_verify.py
#    期望：morph 名 52/52 ARKit；extensionsRequired = EXT_meshopt_compression；
#          skins = 0（head-only）；无 draco
# 2) 渲染对比：Blender 内渲染到文件后 look(image=...)
# 3) 静态服务：https://<本机IP>:5199/ 与 /redpanda_head.glb 均返回 200
# 4) 子路径构建（部署前）：cd aniface-demo && npm run check && $env:BASE_PATH='/<repo>/'; npm run build
#    期望：dist/ 里有 index.html、assets/、redpanda_head.glb、mediapipe/；index.html 资源带 /<repo>/ 前缀
```

## 不要做的事

- 不要用 `Start-Process` 起后台 npm 服务（本机策略会拒绝）；用前台 `exec_command` 起会话。
- 5173 端口属于另一个项目，不要占用或终止其进程。
- 不要把 `certs/`（私钥）、`*.npy`（派生数据）、`node_modules/`、`ICT-FaceKit/` 提交进 git。
- **不要把任何真人照片素材提交进仓库**（`aniface-demo/public/sample.jpg` 这张证件照已从工作区与全部提交历史中移除）。要试演示效果，用「用视频 / 图片文件测试」自己选本地文件，文件不会进仓库。
- **`.blend` 里会藏本机路径**：图片数据块名、`image.filepath`、`scene.render.filepath`、以及打包图片的 `PackedFile.filepath`（Python 改 `image.filepath` 清不掉它，需 unpack→改用相对路径）。清理后用「另存一份未压缩副本再全字符串扫描」验证——**直接扫文件没用，.blend 默认是 zstd 压缩的**。
- 但 `C:\Users\<用户名>\Documents` 消不掉：**任何在本机保存的 .blend 都会写入**（全新空白工程实测同样存在），属 Blender 写 UI 状态的固有行为。
