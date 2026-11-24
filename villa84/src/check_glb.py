"""Open a GLB in a clean Blender scene, report what is inside and render a quick preview (checks the exported file itself)."""
import math
import sys

import bpy
from mathutils import Vector

src, out = sys.argv[1], sys.argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
mn, mx = Vector((1e9,) * 3), Vector((-1e9,) * 3)
tris = 0
for o in meshes:
    tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        mn = Vector(map(min, mn, w))
        mx = Vector(map(max, mx, w))
print("objects", len(bpy.data.objects), "meshes", len(meshes), "materials", len(bpy.data.materials), "triangles", tris)
print("bbox", [round(v, 2) for v in mn], [round(v, 2) for v in mx])
print("top-level:", sorted(o.name for o in bpy.data.objects if o.parent is None))
sc = bpy.context.scene
w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.93, 1.0, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.2
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
sc.collection.objects.link(sun)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
c = (mn + mx) / 2
cam.location = c + Vector((-50, -45, 38))
cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.lens = 30
sc.camera = cam
sc.render.engine = "CYCLES"
sc.cycles.samples = 12
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 800, 500
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
