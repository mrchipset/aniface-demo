# aniface-demo · 小熊猫头像

## 启动

    npm install
    npm run vendor:mediapipe      # 可选但强烈建议：把 MediaPipe 运行时本地化（约 36MB）
    npm run dev

**默认走 HTTPS**（http:// 在非 localhost 下拿不到摄像头 API）。

## 常用脚本

| 命令 | 作用 |
|---|---|
| `npm run dev` | 启动开发服务器（默认 HTTPS，端口 5199） |
| `npm run build` | 构建到 `dist/` |
| `npm run cert` | 重新生成自签证书（本机 IP 变化后执行） |
| `npm run vendor:mediapipe` | 把 MediaPipe 的 WASM 与模型复制/下载到 `public/mediapipe/`，启动不再依赖 CDN |
| `npm run check` | 自检 `main.js` 里所有 `$('id')` 是否都能在 `index.html` 找到（提前发现"引用了已删除元素"这类运行时 TypeError） |

> `public/mediapipe/`（约 36MB）已在 `.gitignore` 中，用 `npm run vendor:mediapipe` 重新生成。
> 未执行该命令时，代码会自动回退到 CDN。

## 操作小技巧

- **滑块支持滚轮**：鼠标悬停直接滚动即可改值（不用按住拖动）
  - `Shift` + 滚轮 = 10 倍步长（粗调）
  - `Alt` + 滚轮 = 1/10 步长（微调）
  - 步长默认取该滑块范围的 1%，所以短距离拖动也能精确定位
- **合成视图可直接拖拽**移动输出选区
- **模型画布可拖拽旋转、滚轮缩放**（误触变太大时点「重置视图」）

    https://localhost:5199/            # 本机
    https://192.168.71.5:5199/         # 局域网（把 IP 换成你机器实际的）

浏览器会提示"证书不受信任"（自签证书）→ 点 **高级 → 继续前往**。
若找不到继续按钮，在警告页直接输入 `thisisunsafe`。

想要纯 HTTP：`HTTPS=0 npm run dev`（PowerShell: `$env:HTTPS='0'; npm run dev`）

## 局域网 IP 变了怎么办

重新生成证书（会把当前所有网卡 IP 写进 SAN）：

    npm run cert
    # 然后重启 npm run dev

## 常见报错

| 报错 | 原因 | 解决 |
|---|---|---|
| `ERR_SSL_PROTOCOL_ERROR` | 用 `https://` 访问了一个 **HTTP** 服务 | 确认服务是 HTTPS 起（看启动日志里是不是 `https://…`）；用 `npm run dev` 默认就是 HTTPS |
| `Cannot read properties of undefined (reading 'getUserMedia')` | 页面**不是安全上下文** | 用 `https://` 或 `http://localhost`；页面顶部会显示 `secure=` 便于判断 |
| `NotAllowedError` | 摄像头权限被拒 | 浏览器地址栏权限图标里允许 |
| `NotReadableError` | 摄像头被其它程序占用 | 关掉微信/腾讯会议/Zoom 等 |

## 三种使用方式

1. **摄像头** —— 需 https / localhost + 浏览器授权
2. **文件模式** —— 选本地视频或图片，MediaPipe 逐帧驱动（不需要摄像头）
3. **手动滑块** —— 直接驱动 jawOpen / eyeBlink / mouthSmile / browInnerUp / headYaw

## 界面说明

三栏布局：

| 区域 | 内容 |
|---|---|
| 左：**摄像头原始画面** | 原始视频 + 关键点叠加（可切换关键点/网格）+ 镜像开关 + 实时信息（分辨率/帧率/检测耗时/人脸/关键点数/设备名） |
| 中：**合成视图** | 原始画面为底，3D 小熊猫按人脸框位置**贴合上去**（AR 叠加） |
| 右：控制面板 | 3D 模型（源）· 合成设置 · 位置缩放 · 手动表情 · 文件模式 |

## 合成视图（把小熊猫贴进画面）

### 背景虚化 ✅ 已实测可用

摄像头面板里新增一组控件：

| 控件 | 作用 |
|---|---|
| ☐ **背景虚化** | 开关。首次勾选会加载 Selfie Segmenter 分割模型（本地 244KB） |
| **虚化强度** | 模糊半径 2~40 px（默认 14） |
| ☐ **反转遮罩** | 万一人物/背景被识别反了，勾这个即可（不同模型版本的极性可能不同） |

**原理**：MediaPipe `ImageSegmenter`（selfie_segmenter）每 2 帧产出一张人物置信度遮罩，
然后用 2D 合成做三层：

1. **底层**：整幅画面的模糊版（`ctx.filter = 'blur(Npx)'`，放大 2 倍 padding 绘制以避免边缘透明描边）
2. **上层**：原画 + 遮罩（`destination-in`）得到"清晰的人物抠图"
3. 叠在一起 = 清晰人物 + 虚化背景

注意：
- 虚化**只作用于「合成视图」**，左边「摄像头原始画面」始终保持原样（方便对比）
- 镜像时遮罩会一起翻转，否则人物区域会左右错位
- 关闭虚化时不跑分割，不额外消耗算力
- 图片模式同样支持（切到 IMAGE 模式跑一次分割）

**原理**：2D 合成，不做 3D 场景重建

1. 底层：把原始视频画进合成画布（按需镜像）
2. 顶层：把 **3D 模型画布**（透明背景）按**人脸框**的位置与大小画上去

模型画布天然透明（aniface 的 `WebGLRenderer` 用 `alpha: true` 且场景没有 background），
所以在 `processLandmarks()`（内部已 render）之后立即 `drawImage` 就能取到内容 ——
同一 JS 任务内读取，**不需要 `preserveDrawingBuffer`**。

**人脸框 → 整个头**：MediaPipe 的 468 个关键点只覆盖面部，
所以框要向上扩 62%、向下扩 18%、左右各扩 32%，才盖得住头发和头顶。

### 合成设置

| 控件 | 作用 |
|---|---|
| **合成** | 开关。关掉就是纯原始画面 |
| **大小** | 小熊猫相对人脸的大小（默认 1.8） |
| **偏移 X / Y** | 位置微调（范围 ±0.6，即画布宽/高的 ±60%） |
| **重置合成** | 恢复默认 |

底部有一行**实时诊断**，显示 `脸框[…] 大小… 偏移… | 贴到 (x,y) 宽x高 画布… 镜像…`，
用于确认参数是否生效。

### 和「位置 / 缩放（模型自身）」的区别

| | 作用范围 |
|---|---|
| **合成设置** | 模型**贴到画面上的位置/大小** ← 对不准时优先用这个 |
| **位置 / 缩放** | 模型在**它自己那张画布内**的位置/大小（会连带影响贴上去的内容） |

### 镜像规则（易踩坑）

两处镜像必须**相反**，否则会出现双重镜像、动作与画面相反：

1. **人脸框的 x 坐标**：画面镜像时要一起翻转（`cx = 1 - cx`）
2. **贴模型时的翻转**：`pasteMirror = !viewMirror`

原因：aniface 的 head-only 分支内部已经对 Y/Z 取过负（`y = -y, z = -z`）。

## 输出视图（选区裁剪 × 倍率）

从**合成视图**里框选一块区域，按倍率放大后输出到独立画布 —— 相当于一个"虚拟取景窗"。

| 控件 | 作用 |
|---|---|
| **选区宽 / 高** | 选区的像素尺寸（50~1920，默认 400×400），单位是合成画布的像素 |
| **位置 X / Y** | 选区中心（0~1，默认居中） |
| **输出倍率** | 0.25~4，输出画布 = 选区尺寸 × 倍率 |
| **重置选区** | 回到 400×400 居中、倍率 1 |

### 蒙版（圆角 / 圆形）

| 控件 | 作用 |
|---|---|
| **蒙版** | `无` / `圆角矩形` / `圆形` |
| **圆角** | 圆角半径，按短边的百分比（0~50%，默认 18%） |
| **边缘羽化** | 0~30 px，把边缘做柔化，避免生硬锯齿 |

实现要点：
- 蒙版用的是 **`destination-in`**（把形状当 alpha 遮罩乘上去），所以形状**外部保持透明**，
  输出画布右侧是棋盘格背景，能直观看出抠出来的形状
- 羽化 = 在离屏遮罩上用 `ctx.filter = 'blur(Npx)'` 画形状，再叠加
- `roundRect` 不可用时自动回退到手工二次曲线路径
- **圆形是按输出矩形内切椭圆**：选区是正方形时是正圆，非正方形则是椭圆

**交互**：
- 合成视图里会画出选区（**框外压暗 + 蓝色虚线框 + 尺寸标注**）
- **可直接在合成视图上拖拽**移动选区，滑块用于精确定位
- 右侧 `sel_info` 实时显示 `选区 → 输出` 尺寸，例如 `400×400 → 800×800`

**实现要点**：
- 每帧顺序必须是 **先 `drawComposite()`（干净画面）→ 再 `drawOutput()` 裁剪 → 最后 `drawSelectionOverlay()` 画框**，
  否则选区框会被一起裁进输出里
- 输出画布按 `选区×倍率` 设置固有分辨率，CSS 再缩放到侧栏宽度显示
- `selRect()` 会把选区钳制在画布内，避免越界出现空白

## 排错

| 现象 | 原因 / 处理 |
|---|---|
| 小熊猫固定在画布左上角、偏移滑块没反应 | 贴图分支漏了 `translate`（已修：两条分支都要 translate） |
| 必须把 Scale 调到 0.1 才看得见，只见一张大嘴 | aniface head-only 会把矩阵放大 40 倍（已修：自动抵消内层缩放） |
| 模型在画布内跑偏、被裁成半张脸 | 人脸矩阵的平移分量被写进模型根节点（已修：清零 `matrix.elements[12..14]`） |
| 模型巨大/全黑 | 可能是滚轮误触把相机拉近了，点「重置视图」 |
| 启动卡在「初始化 MediaPipe」 | 未跑 `npm run vendor:mediapipe`，走 CDN 受网络影响 |
| `Cannot set properties of null` | 改布局后残留的失效元素引用，跑 `npm run check` 定位 |

## 模型

`public/redpanda_head.glb` —— 52 个 ARKit 表情（含 tongueOut）、head-only、meshopt 压缩、1.37 MB

## 部署到 GitHub Pages

线上地址形如 `https://<用户名>.github.io/<仓库名>/`。
**Pages 自带 HTTPS，所以摄像头 API 在别人机器上直接可用**——比自己签证书让别人访问省事得多。

### 一次性准备

1. 在 GitHub 建一个**公开**空仓库（Pages 免费版只对公开仓库开放），**不要**勾选 Add README
2. 本地加远程并推送（注意：仓库根目录是 `blender/`，`aniface-demo/` 是它的子目录，直接整个推）

       cd C:\Users\Zouyu\tmp\blender
       git remote add origin https://github.com/<用户名>/<仓库名>.git
       git push -u origin main

3. ~~手动开 Pages~~ **不用**：工作流里的 `configure-pages` 带 `enablement: true`，会自动开启并设为 GitHub Actions 源。
   若自动开启失败（提示 `Pages site not found`），再去 **Settings → Pages → Source** 手动选 **GitHub Actions** 并重跑
4. 首次推送会自动触发 `Deploy aniface demo to GitHub Pages`；也可在 **Actions** 页手动 `Run workflow`
5. 等 1~2 分钟后访问 `https://<用户名>.github.io/<仓库名>/`

### CI 里做了什么（见仓库根 `.github/workflows/deploy-pages.yml`）

| 步骤 | 说明 |
|---|---|
| `npm ci` | 按 `package-lock.json` 干净安装 |
| `npm run vendor:mediapipe` | **构建时**生成约 36MB 的 MediaPipe 运行时（WASM 从 `node_modules` 复制，模型从 Google 官方下载）——所以这些大文件**不需要进 git** |
| `npm run check` | 校验所有 `$('id')` 引用，防止"引用了已删除元素"上线 |
| `BASE_PATH=/<仓库名>/ npm run build` | 子路径构建，仓库名自动取自当前仓库，**换仓库名不用改配置** |
| `upload-pages-artifact` + `deploy-pages` | 只发布 `aniface-demo/dist` |

### 子路径是怎么处理的

GitHub Pages 把站点挂在 `/<仓库名>/` 下，根绝对路径（`/redpanda_head.glb`）会 404。
所以：

- `vite.config.js` 读环境变量 `BASE_PATH` 作为 `base`（默认 `/`，本地开发不受影响）
- `src/main.js` 用 `const BASE = import.meta.env.BASE_URL` + `asset('x')` 拼所有静态资源路径
  （模型、样例图、MediaPipe 的 wasm/模型）

**新增任何静态资源都要走 `asset()`**，不要写 `/xxx` 这种根路径。

### 本地验证线上行为

    cd aniface-demo
    $env:BASE_PATH='/<仓库名>/'; $env:HTTPS='0'; npm run build
    node node_modules\vite\bin\vite.js preview --port 4173 --strictPort
    # 打开 http://localhost:4173/<仓库名>/   —— 资源应该全部 200

### 注意事项

- 部署内容 **37.7 MB**（主要是 MediaPipe 运行时），远低于 Pages 的站点体积上限
- 仓库里**不含**上述大文件，`git push` 只有约 22 MB
- 走 CDN 兜底也能用，但 `vendor:mediapipe` 更稳（不用看 Google/jsDelivr 的网络脸色）
- 若以后换到自定义域名 / 根路径部署，把 `BASE_PATH` 设为 `/` 即可
