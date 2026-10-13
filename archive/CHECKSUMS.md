# 归档校验和 (SHA256)

归档时间: 2026-10-06
归档版本: redpanda-v1
原始归档提交: 3a693e4（**已失效** —— 2026-10-12 隐私清理重写历史后哈希全部变更）

> 2026-10-13 目录整理：根目录的脚本与素材移入 `work/`（`work/scripts/`、`work/assets/`），
> 表格中的路径已同步更新。**文件内容与 SHA256 均未变化**，仍是归档时的同一批产物。

| 文件 | 字节 | SHA256 |
|---|---|---|
| `work/assets/redpanda_head.glb` | 881812 | `D3E3B7097169B169C8CF4F28DC11F6315AC91F7008AB016A718C2D1983D320EE` |
| `aniface-demo/public/redpanda_head.glb` | 881812 | `D3E3B7097169B169C8CF4F28DC11F6315AC91F7008AB016A718C2D1983D320EE` |
| `aniface_head.glb` | 21199364 | `143806A4786FCEFF68879895F0FC9B215B13850DF2C26175E04D8222EE5934E1` |
| ~~`aniface_head.glb`~~ | — | **已于 2026-10-12 从仓库历史移除**（内嵌本人照片，隐私处理） |
| `work/assets/raccoon_head_small.glb` | 631220 | `D5BF89AD8D3BC5DBAB936CC08E267851129DA24F200F598488848F94FEB8754D` |
| `work/assets/rpm_avatar.glb` | 2621520 | `15CCB2ADA1EDE2529ADA0DF630A528EB98BB23C997DFAA5BC0637D15AF0A5104` |
| `work/assets/redpanda_base3.png` | 82888 | `FA9199D7229A59FDEFA15B69498F16CFC362285349D476566337865D87A8C886` |
| `work/assets/redpanda_ear3.png` | 94408 | `46342699C6AF00031294931C95A98D20A60077E2AF21C42AC48D2659630C1988` |

## 说明

- `redpanda_head.glb`: 小熊猫头像，52 个 ARKit 表情，head-only，meshopt 压缩
- 两份 redpanda_head.glb 内容相同（`work/assets/` 为源，aniface-demo/public 为演示用副本）
- ~~`aniface_head.glb`~~：人类头像（51 个 ARKit 表情），**已从历史移除** —— 它把一张真人照片内嵌为贴图
- 贴图为当前生效的 final_f 配色版本

## Blender 源工程

| 文件 | 字节 | SHA256 |
|---|---|---|
| `work/assets/redpanda_source.blend` | 8193159 | `8B4E588FDF03D129F5BC8DE5F14D26FB1327A52EB27FF95B70A841C1192ED3E9` |
| `work/assets/textures/studio_kontrast_03_1k.hdr` | 1473616 | （PolyHaven CC0 环境贴图，见下）|

- 2026-10-12 由 `Untitled.blend` 另存改名而来（原名已删除）
- 内容：小熊猫 4 个部件（`head_geo.002` 5304 顶点 / 53 个 shape key、`ears_geo`、`hair_geo`、`tufts_geo`）+ 材质与贴图引用
- 注意：该文件是**实验累积场景**，除小熊猫外还包含人类头像（`AnifaceHead`）、RPM 全身像部件、金属 `Cube`、`Icosphere` 等历史对象
- **2026-10-13 隐私清理**（指纹已更新为上面的新值）：
  - 删除 2 个指向本机的图片数据块：`Weixin Image_20260118215538_47_32 (1).jpg`（本人照片，被 `PhotoFace` 材质引用）与 `codex-clipboard-WBfeXA.png`（剪贴板临时图，被 `PortraitFace` 引用）
  - 清空 scene 的 `render.filepath`（原为 `C:\Users\...\final_34.png`）
  - 环境贴图由「打包 + 记录绝对路径」改为**相对路径 `//textures/studio_kontrast_03_1k.hdr`**，所以多了上面那个 1.4 MB 的 HDR 文件（CC0，可自由再分发）
  - 副作用：`PhotoFace` / `PortraitFace` 两个材质的贴图节点变为空（这两张贴图本来就已失效，且照片投影方案已废弃）；一个无引用的孤儿图片 `Image_1` 被 Blender 自动清理
  - 场景结构未变：21 个对象、28 个材质、`head_geo.002` 仍是 53 个 shape key
  - ⚠️ 仍无法消除：任何在本机保存的 .blend 都会记录 `C:\Users\Zouyu\Documents`（Blender 写 UI 状态时的固有行为，用全新空白工程实测同样存在）

## Blender 源工程（干净版）

| 文件 | 字节 | SHA256 |
|---|---|---|
| `work/assets/redpanda_only.blend` | 1972291 | `7C37C968EE9EF33FC5432439368BB2F93D5B0352FE4C66CEBC611E3CF97388EC` |

- 由 `redpanda_source.blend` 删减而来：移除 14 个无关对象（人类头像、RPM 部件、Cube、Icosphere、HeadCam 等）
  并清理 2645 个孤立数据块
- 保留：小熊猫 4 部件 + `raccoon_head` 空物体 + `Camera`（已对准）+ `Light` + 环境光
- `head_geo.002`：5304 顶点、**53 个 shape key 完好**、材质仅 `MAT_Racoon.004`（无残留空槽）
- 体积 8.77 MB → **1.88 MB**
- 附带 `redpanda_only_preview.png`（打开即渲染的验证图）

