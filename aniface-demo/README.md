# aniface-demo · 小熊猫头像

## 启动

    npm install
    npm run dev

**默认走 HTTPS**（http:// 在非 localhost 下拿不到摄像头 API）。

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

## 模型

`public/redpanda_head.glb` —— 52 个 ARKit 表情（含 tongueOut）、head-only、meshopt 压缩、1.37 MB
