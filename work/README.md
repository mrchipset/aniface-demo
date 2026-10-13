# work/ · 建模工作目录

原来堆在仓库根目录的 66 个 Python 脚本与 50 个素材 / 渲染图都收在这里，
根目录只保留文档与可交付的 `aniface-demo/`。

```
work/
├── assets/                 ← 脚本的“当前目录”（CWD）
│   ├── *.glb / *.blend     模型与 Blender 源工程
│   ├── *.png               贴图（racc_tex_*、redpanda_base*、redpanda_ear*…）与参考图
│   ├── *.npy / *.npz / *.json  中间数据（多数在 .gitignore 中，可由脚本重建）
│   └── renders/            迭代过程中的渲染与预览图（纯留档，没有脚本读取）★
└── scripts/
    ├── pipeline.py         ★ 真人头像一键重建（主线入口）
    ├── facekit/            人头流水线：ICT 身份拟合、对齐、贴图、瘦身导出
    ├── redpanda/           小熊猫流水线：配色重映射、UV 绘制、导出（含逐版本迭代）
    └── tools/              GLB 规格校验与分析、贴图导出等通用工具
```

## 为什么 `assets/` 是扁平的

历史脚本一律用**裸文件名**读写素材（例如 `Image.open("racc_tex_Image_0_001.png")`、
`np.save("ict_ids.npy", ids)`），路径相对于**运行进程的当前目录**。
把素材拆到子目录会让这 60 多个脚本一起失效，所以 `assets/` 保持扁平：
**它就是脚本们约定俗成的 CWD**。只有确定没有任何脚本读取的渲染图才放进 `renders/`（★）。

`redpanda_only.blend` / `redpanda_source.blend` 用 `//` 相对路径引用贴图，
因此**必须和贴图待在同一个目录**——这也是它们留在 `assets/` 顶层的原因。

## 怎么跑

主线的 4 个脚本已经**自带路径自定位**（从任意目录运行都能找到 `work/assets`），
其余历史脚本请先切到 assets 再运行。

```powershell
# 1) 真人头像一键重建（在 Blender 里执行；建议先设好照片路径）
#    $env:PHOTO = "C:\path\to\your-face.jpg"
exec(open(r"work/scripts/pipeline.py", encoding="utf-8").read())

# 2) GLB 规格校验（morph 名 / 压缩扩展 / skin），默认校验 work/assets/redpanda_head.glb
uv run --python 3.11 --with numpy python work\scripts\tools\glb_verify.py

# 3) 人脸关键点 → ICT 身份系数（需先设置 PHOTO）
uv run --python 3.11 --with "mediapipe==0.10.14" --with pillow --with numpy python work\scripts\facekit\mp_lm.py
uv run --python 3.11 --with numpy python work\scripts\facekit\fit3.py
```

跑历史脚本（`/redpanda/`、部分 `/facekit/`）时，把工作目录设为 `work/assets`：

```powershell
cd work\assets
# 然后在 Blender 里 exec(open(r"..\scripts\redpanda\rp_v4.py", encoding="utf-8").read())
```

> ⚠️ 不要在这里生成或提交真人照片：`mp_lm.py` 会输出调试图 `lm_check.png`，
> 这类文件已在 `.gitignore` 中屏蔽，仓库不放任何真人照片素材。
