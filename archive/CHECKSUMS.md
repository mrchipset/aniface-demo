# 归档校验和 (SHA256)

归档时间: 2026-10-06
归档版本: redpanda-v1
本次提交: 3a693e4

| 文件 | 字节 | SHA256 |
|---|---|---|
| `redpanda_head.glb` | 881812 | `D3E3B7097169B169C8CF4F28DC11F6315AC91F7008AB016A718C2D1983D320EE` |
| `aniface-demo/public/redpanda_head.glb` | 881812 | `D3E3B7097169B169C8CF4F28DC11F6315AC91F7008AB016A718C2D1983D320EE` |
| `aniface_head.glb` | 21199364 | `143806A4786FCEFF68879895F0FC9B215B13850DF2C26175E04D8222EE5934E1` |
| `raccoon_head_small.glb` | 631220 | `D5BF89AD8D3BC5DBAB936CC08E267851129DA24F200F598488848F94FEB8754D` |
| `rpm_avatar.glb` | 2621520 | `15CCB2ADA1EDE2529ADA0DF630A528EB98BB23C997DFAA5BC0637D15AF0A5104` |
| `redpanda_base3.png` | 82888 | `FA9199D7229A59FDEFA15B69498F16CFC362285349D476566337865D87A8C886` |
| `redpanda_ear3.png` | 94408 | `46342699C6AF00031294931C95A98D20A60077E2AF21C42AC48D2659630C1988` |

## 说明

- `redpanda_head.glb`: 小熊猫头像，52 个 ARKit 表情，head-only，meshopt 压缩
- 两份 redpanda_head.glb 内容相同（根目录为源，aniface-demo/public 为演示用副本）
- `aniface_head.glb`: 人类头像，51 个 ARKit 表情（缺 tongueOut）
- 贴图为当前生效的 final_f 配色版本

## Blender 源工程

| 文件 | 字节 | SHA256 |
|---|---|---|
| `redpanda_source.blend` | 9191340 | `601953B545F0E30F4FC60B32703C9CB05397389016D9C36FC5E3338BE7F4CC8C` |

- 2026-10-12 由 `Untitled.blend` 另存改名而来（原名已删除）
- 内容：小熊猫 4 个部件（`head_geo.002` 5304 顶点 / 53 个 shape key、`ears_geo`、`hair_geo`、`tufts_geo`）+ 材质与贴图引用
- 注意：该文件是**实验累积场景**，除小熊猫外还包含人类头像（`AnifaceHead`）、RPM 全身像部件、金属 `Cube`、`Icosphere` 等历史对象
