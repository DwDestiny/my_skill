# Blender 无头管线（技术卡 T23）

何时读：页面需要一个自制三维模型，而 three.js 程序化几何做不出来。
读完做什么：照"接入页面的三步"生成 glb，再用 `gltf-model-stage` 的加载端显示。
示例：`examples/mechanisms/blender-headless-glb/`（`make-model.py`、`model.glb`、`index.html`）。
验证日期：2026-10-16，Blender 4.0.2。

## 1. 何时用 Blender

| 情况 | 选择 |
|---|---|
| 环面、球、圆柱、简单挤出 | three.js 程序化几何 |
| 带倒角的硬表面件、多个部件叠放 | Blender |
| 需要布尔、阵列、倒角修改器 | Blender |
| 需要贴图烘焙、有机形体、骨骼动画 | 示例环境不做，另找资产 |
| 模型只显示一次，形状极简 | three.js 程序化几何 |

## 2. 无头命令

```
blender -b --python make-model.py
blender -b --python make-model.py -- --no-render
```

- `-b` 表示无界面。`--` 之后的参数交给脚本，用 `sys.argv` 读取。
- bpy 只能在 Blender 进程里用。系统 Python 3.12 没有 bpy。`pip install bpy` 不可用（示例环境已验证：无 pip，且 bpy 要求更高版本 Python）。
- 在脚本里用 `os.path.dirname(os.path.abspath(__file__))` 取输出目录。

## 3. bpy 脚本骨架

1. `bpy.ops.wm.read_factory_settings(use_empty=True)`：清空默认场景。
2. 建材质：`use_nodes=True`，取 `Principled BSDF`，设 `Base Color`、`Roughness`、`Metallic`。不贴图。
3. 建几何：`bpy.ops.mesh.primitive_cube_add`、`primitive_cylinder_add`。设 `scale`、`rotation_euler`。
4. 加修改器：`obj.modifiers.new("Bevel", "BEVEL")`，设 `width`、`segments`。
5. 导出：`bpy.ops.export_scene.gltf(filepath=..., export_format='GLB', export_apply=True)`。
6. 打印体积：`os.path.getsize`。体积超限就减细分。

> **注意**：Blender 是 Z 向上，glTF 是 Y 向上。官方导出器自动转轴。自写写入器要把 `(x, y, z)` 转成 `(x, z, -y)`。

## 4. 官方导出器与 numpy

| 事实 | 状态 |
|---|---|
| 官方 glTF 导出器需要 numpy | 示例环境已验证 |
| 示例环境 Blender 用系统 Python 3.12。2026-10-16 之前没有 numpy，官方导出器抛 `ModuleNotFoundError: No module named 'numpy'` | 示例环境已验证 |
| 2026-10-16 用 `sudo apt-get install python3-numpy`（1.26.4）后，官方导出器可用。`make-model.py` 重跑输出 `model.glb` 49276 字节 | 示例环境已验证 |
| 示例脚本仍保留标准库写入器 `write_glb_fallback`：官方导出器失败时自动改用 | 示例环境已验证 |
| 写入器只支持网格、法线、一个 PBR 材质，不支持贴图、动画、骨骼 | 示例环境已验证 |

处理办法：

1. 默认走官方导出器。贴图、动画、骨骼都可用。
2. 别的机器没有 numpy 时，脚本自动退到 `write_glb_fallback`，只出网格与纯色材质。要官方导出器就装 `python3-numpy`。
3. 不要自行安装 numpy 以外的软件。

## 5. 渲染预览

| 参数 | 值 | 状态 |
|---|---|---|
| 引擎 | `CYCLES`，`sc.cycles.device = "CPU"` | 示例环境已验证 |
| 采样 | `sc.cycles.samples = 16` | 示例环境已验证 |
| 降噪 | `sc.cycles.use_denoising = False` | 示例环境已验证：示例环境 Blender 无 OpenImageDenoise，开启会报错 |
| 分辨率 | 640 x 400 | 示例环境已验证 |
| 耗时 | 约 70 秒（2 核 CPU，示例场景） | 示例环境已验证 |
| EEVEE 与 Workbench | 无显示环境下不可用 | 示例环境已验证（2026-10-16）：缺 `libEGL.so.1`，`blender -b` 一进渲染就崩溃（dumped core）。装 `libegl1` 是系统变更，先问用户 |

- 16 采样的图有颗粒。预览用来看形状与材质，不当成品图。
- 要无颗粒，把采样提到 32 并接受更长耗时。960 x 600、32 采样在 2 核上超过 400 秒（2026-10-16 实测超时），机器有其他负载时更慢。首屏静帧不要指望 Blender 渲染，用 three.js 画布截取。
- 预览图不进页面。它用于文档和自检。

## 6. glb 体积控制

| 手段 | 说明 | 状态 |
|---|---|---|
| 降低 Bevel `segments` | 3 段够用。每加 1 段，面数明显增加 | 示例环境已验证 |
| `export_apply=True` | 导出时应用修改器 | 示例环境已验证（装 numpy 后官方导出器走通） |
| 合并重复顶点 | 写入器按位置加法线去重 | 示例环境已验证 |
| 不导灯与相机 | `export_cameras=False`、`export_lights=False` | 未验证（官方导出器不可用） |
| Draco：`export_draco_mesh_compression_enable=True` | 需要 Blender 自带 Draco 库 | 示例环境已验证：未找到 `libextern_draco`，不可用 |

- 示例结果：6 块倒角薄板加 1 根柱，`model.glb` 40660 字节，不压缩。
- 目标：首屏用的 glb 不超过 1 MB。
- 如果页面要加载压缩模型，要另加 DRACOLoader 或 meshopt（见 `gltf-model-stage`）。

## 7. 接入页面的三步

1. 改 `make-model.py` 的建模段，运行 `blender -b --python make-model.py`，得到 `model.glb`。
2. 把 `model.glb` 放在页面同目录。复制 `index.html` 的 importmap、loader、灯光。
3. 用 `python3 -m http.server` 打开页面。检查画布有模型，console 0 error。保留 Reduce Motion 分支。

> **注意**：`file://` 下浏览器禁止加载 glb。必须经 http 访问。

## 8. 示例环境限制

| 限制 | 状态 |
|---|---|
| 2 核、3 GB 内存、无 GPU | 示例环境已验证 |
| Cycles CPU 可用，但只够 640 x 400、16 采样的预览（约 70 秒） | 示例环境已验证 |
| EEVEE 与 Workbench 不可用（缺 `libEGL.so.1`，崩溃） | 示例环境已验证 |
| 首屏静帧 | 用 three.js 画布截取，不用 Blender 渲染 |
| 页面里 WebGL 是软件渲染，金属材质无环境图会偏暗 | 示例环境已验证：示例把 Metallic 降到 0.3 |
| Draco 压缩 | 示例环境已验证：不可用 |
| 官方 glTF 导出器 | 示例环境已验证：装 `python3-numpy` 后可用 |

## 9. 资产写进 ASSETS.md 的字段

| 字段 | 内容 |
|---|---|
| 路径 | 相对页面目录的 `model.glb` |
| 来源 | `Blender 4.0.2 无头，make-model.py` |
| 生成命令 | `blender -b --python make-model.py` |
| 体积 | 字节数 |
| 面数 | 三角形数（未统计则写"未核"） |
| 材质 | 名称、颜色、Roughness、Metallic |
| 压缩 | 无 / Draco / meshopt |
| 日期 | 生成日期 |
| 用在哪 | 页面与章节 |
