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
