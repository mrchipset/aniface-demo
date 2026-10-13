# Blender + Aniface 头像实验

用 Blender MCP（`mcp-for-blender`）驱动 Blender，把照片/参考图做成**能被浏览器摄像头驱动的 3D 头像**（aniface）。

## 文档

- [AGENTS.md](AGENTS.md) —— 项目级工作约定与踩坑清单（动手前先读）
- [docs/STATUS.md](docs/STATUS.md) —— 当前问题清单 + 两条流水线的实现步骤

## 目录结构

```
.
├── aniface-demo/              可运行的 aniface 演示（Vite + three.js + MediaPipe）
│   ├── src/main.js            三种驱动模式：摄像头 / 文件 / 手动滑块；含位置·缩放控制
│   ├── public/
│   │   ├── redpanda_head.glb  ★ 小熊猫头像（52 个 ARKit 表情）
│   │   └── sample.jpg
│   ├── certs/                 自签 HTTPS 证书（已 gitignore，用 npm run cert 生成）
│   └── README.md              启动 / 跨机器访问 / 排错
│
├── pipeline.py                ★ 人类头像一键重建（装载→拟合→缩放→法线→投影→重命名→导出）
├── rp_*.py                    小熊猫制作过程脚本
├── fit3.py / mp_lm.py         MediaPipe 关键点 → ICT 身份系数拟合
│
├── redpanda_head.glb          ★ 小熊猫头像（0.84 MB，meshopt）
├── redpanda_only.blend        ★ 小熊猫 Blender 源工程 · 干净版（1.88 MB，开箱可渲染）
├── redpanda_source.blend      ★ 小熊猫 Blender 源工程（8.8 MB，含 53 个 shape key）
├── raccoon_head_small.glb     基座模型（aniface 官方 demo 素材，MIT）
├── rpm_avatar.glb             Ready Player Me 全身像（来源确证，作参考）
│
├── redpanda_base3.png         小熊猫主体贴图（重映射生成）
├── redpanda_ear3.png          耳朵贴图（白边橘心）
├── racc_tex_Image_0.png       原始 raccoon 贴图（配色映射的输入）
│
├── final_f.png / final_34.png 小熊猫最终渲染
├── ict_now_f.png / slim_f.png 人类头像渲染
└── render_metal_cube.png      金属 Cube 测试渲染
```

## 快速开始（看小熊猫）

```
cd aniface-demo
npm install
npm run dev            # 默认 HTTPS，打开 https://localhost:5199/
```

## 在线演示（GitHub Pages）

推送到 GitHub 后由 Actions 自动构建并发布到 `https://<用户名>.github.io/<仓库名>/`。
Pages 自带 HTTPS，**别人打开网页就能直接授权摄像头驱动头像**，不用再处理自签证书。

一键流程：建公开空仓库 → `git remote add origin …` → `git push -u origin main` →
仓库 Settings → Pages → Source 选 **GitHub Actions**。

详细说明见 [aniface-demo/README.md](aniface-demo/README.md#部署到-github-pages)，
工作流见 [.github/workflows/deploy-pages.yml](.github/workflows/deploy-pages.yml)。
工作流会在 CI 里现跑 `npm run vendor:mediapipe` 生成约 36MB 运行时，所以这些大文件不入库。

跨机器用摄像头（需要 https）：
```
npm run cert           # 本机 IP 变了之后重新生成证书
npm run dev
# 在另一台机器打开 https://<本机IP>:5199/
```

## 依赖的外部资源

| 资源 | 用途 | 许可 |
|---|---|---|
| `ICT-FaceKit`（需自行 clone） | 人头基座 + 53 个 ARKit 表情 | MIT |
| `raccoon_head_small.glb` | 小熊猫基座（自带 52 个 ARKit 表情） | 随 aniface 仓库，MIT |
| `rpm_avatar.glb` | 参考用全身像 | Ready Player Me 条款 |
| `mcp-for-blender` | 驱动 Blender 的 MCP 服务 | MIT |

重建 ICT-FaceKit：

    git clone --depth 1 https://github.com/USC-ICT/ICT-FaceKit.git

## 复现人类头像

```
# 在 Blender（已装 mcp-for-blender）里执行
exec(open(r"pipeline.py", encoding="utf-8").read())
```
需要：`ICT-FaceKit/` 已 clone、`ict_fit.json`、`ict_neutral.npy` / `ict_ids.npy`（由 `fit3.py` 生成）、一张正面照片。

## 已知不足

- 小熊猫的**精细斑纹**（白眉斑 / 额中纹 / 白颊）未做——按 3D 坐标程序化绘制精度不够（已尝试并回退），需要在 UV 贴图上手工绘制
- 小熊猫耳朵是**侧向**的（继承自 raccoon），真正小熊猫是直立耳
- `tongueOut` 仅小熊猫版本有，人类版本缺
- 人类头像脸型偏窄长（29 个 2D 约束拟合的局限）

