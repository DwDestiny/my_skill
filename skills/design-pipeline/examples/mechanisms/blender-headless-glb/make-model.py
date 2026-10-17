# 用法：blender -b --python make-model.py
# 只导出 glb、不渲染：blender -b --python make-model.py -- --no-render
# 作用：程序化生成"图层塔"，导出 model.glb，并用 Cycles CPU 渲一张 preview.png。
# 只能在 Blender 进程里运行。系统 Python 没有 bpy。
import bpy, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "model.glb")
PREVIEW = os.path.join(HERE, "preview.png")
RENDER = "--no-render" not in sys.argv

# 1. 清空默认场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 2. 材质：一个主体材质，不贴图
mat = bpy.data.materials.new("Body")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.86, 0.38, 0.16, 1)
bsdf.inputs["Roughness"].default_value = 0.35
bsdf.inputs["Metallic"].default_value = 0.3

# 3. 建模：6 块薄板螺旋错位叠放，中间一根细柱。每个物体加 Bevel 修改器
N, H, GAP = 6, 0.16, 0.10
TOP = N * (H + GAP)

def finish(obj, name):
    obj.name = name
    obj.data.materials.append(mat)
    bev = obj.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.03
    bev.segments = 3
    bev.limit_method = "ANGLE"
    for p in obj.data.polygons:
        p.use_smooth = True

for i in range(N):
    s = 1.0 - i * 0.1  # 越往上越小
    z = i * (H + GAP) + H / 2 - TOP / 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z))
    o = bpy.context.active_object
    o.scale = (1.6 * s, 1.6 * s, H)
    o.rotation_euler[2] = math.radians(i * 22)
    finish(o, "Layer%d" % i)

bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=TOP + 0.3, vertices=32,
                                    location=(0, 0, 0.1))
finish(bpy.context.active_object, "Core")

# 4. 导出 glb。
#    官方导出器 bpy.ops.export_scene.gltf 需要 numpy。本机的 Blender 用系统 Python，没有 numpy。
#    所以先试官方导出器，失败时用下面的纯标准库写入器（读取已应用修改器的网格）。
#    Blender 的 Z 向上，glTF 的 Y 向上：(x, y, z) 转成 (x, z, -y)。
def write_glb_fallback(path):
    import json, struct
    dg = bpy.context.evaluated_depsgraph_get()
    pos, nor, idx, key = [], [], [], {}
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        if hasattr(me, 'calc_normals_split'):
            me.calc_normals_split()  # Blender 4.0 需要先算拆分法线
        me.calc_loop_triangles()
        mw, nm = ob.matrix_world, ob.matrix_world.to_3x3()
        for tri in me.loop_triangles:
            for li, vi in zip(tri.loops, tri.vertices):
                p = mw @ me.vertices[vi].co
                n = (nm @ (me.corner_normals[li].vector if hasattr(me, 'corner_normals') and len(me.corner_normals) else me.loops[li].normal)).normalized()
                k = (round(p.x, 5), round(p.y, 5), round(p.z, 5),
                     round(n.x, 3), round(n.y, 3), round(n.z, 3))
                if k not in key:
                    key[k] = len(pos) // 3
                    pos += [p.x, p.z, -p.y]
                    nor += [n.x, n.z, -n.y]
                idx.append(key[k])
        ev.to_mesh_clear()
    pb = struct.pack("<%df" % len(pos), *pos)
    nb = struct.pack("<%df" % len(nor), *nor)
    ib = struct.pack("<%dI" % len(idx), *idx)
    blob = ib + pb + nb
    xs, ys, zs = pos[0::3], pos[1::3], pos[2::3]
    bc = bsdf.inputs["Base Color"].default_value
    gltf = {
        "asset": {"version": "2.0", "generator": "make-model.py (Blender %s)" % bpy.app.version_string},
        "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "LayerTower"}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 1, "NORMAL": 2}, "indices": 0, "material": 0}]}],
        "materials": [{"name": "Body", "pbrMetallicRoughness": {
            "baseColorFactor": [bc[0], bc[1], bc[2], 1],
            "metallicFactor": bsdf.inputs["Metallic"].default_value,
            "roughnessFactor": bsdf.inputs["Roughness"].default_value}}],
        "buffers": [{"byteLength": len(blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(ib), "target": 34963},
            {"buffer": 0, "byteOffset": len(ib), "byteLength": len(pb), "target": 34962},
            {"buffer": 0, "byteOffset": len(ib) + len(pb), "byteLength": len(nb), "target": 34962}],
        "accessors": [
            {"bufferView": 0, "componentType": 5125, "count": len(idx), "type": "SCALAR"},
            {"bufferView": 1, "componentType": 5126, "count": len(pos) // 3, "type": "VEC3",
             "min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)]},
            {"bufferView": 2, "componentType": 5126, "count": len(nor) // 3, "type": "VEC3"}],
    }
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    blob += b"\0" * (-len(blob) % 4)
    total = 12 + 8 + len(js) + 8 + len(blob)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<I4s", len(js), b"JSON") + js)
        f.write(struct.pack("<I4s", len(blob), b"BIN\0") + blob)

try:
    bpy.ops.export_scene.gltf(
        filepath=OUT, export_format="GLB", export_apply=True,
        export_cameras=False, export_lights=False,
    )
except Exception as e:
    print("OFFICIAL_EXPORT_FAILED", str(e).strip().splitlines()[-1])
    write_glb_fallback(OUT)
print("GLB_BYTES", os.path.getsize(OUT))

# 5. 预览渲染：Cycles CPU，16 采样，640x400
if RENDER:
    sc = bpy.context.scene
    bpy.ops.object.camera_add(location=(5.0, -5.0, 2.6))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(72), 0, math.radians(45))
    sc.camera = cam
    bpy.ops.object.light_add(type="AREA", location=(3, -3, 6))
    light = bpy.context.active_object
    light.data.energy = 800
    light.data.size = 4
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.8, 0.8, 1)
    sc.world = world
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 16
    sc.cycles.use_denoising = False  # 本机 Blender 无 OpenImageDenoise
    sc.render.resolution_x, sc.render.resolution_y = 640, 400
    sc.render.filepath = PREVIEW
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", PREVIEW)
