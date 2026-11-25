"""Small Blender helper library for the villa renders: materials, simple vegetation, sky and sun, camera, Cycles render, glTF import."""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

scene = None
VEG = {}
TREE_POS = []


def reset():
    global scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_set(1)
    VEG.clear()
    TREE_POS.clear()
    return scene


def link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


# ============================================================================ materials
def set_in(node, name, value):
    sock = node.inputs.get(name)
    if sock is not None:
        try:
            sock.default_value = value
        except Exception:
            pass


def new_material(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    return m


def clear_nodes(m):
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return nt, nt.nodes.new("ShaderNodeOutputMaterial")


def _coords(nt):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    return tc.outputs["Object"]


def _variation(nt, color, var, scale, coord):
    """Base colour with low-frequency noise variation."""
    noise = nt.nodes.new("ShaderNodeTexNoise")
    set_in(noise, "Scale", scale)
    set_in(noise, "Detail", 3.0)
    nt.links.new(coord, noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    lo = tuple(max(0.0, c * (1 - var)) for c in color)
    hi = tuple(min(1.0, c * (1 + var)) for c in color)
    ramp.color_ramp.elements[0].color = (*lo, 1)
    ramp.color_ramp.elements[1].color = (*hi, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    return ramp.outputs["Color"]


def _bump(nt, strength, scale, coord, height=None):
    b = nt.nodes.new("ShaderNodeBump")
    set_in(b, "Strength", min(1.0, strength))
    set_in(b, "Distance", 0.02)
    if height is None:
        n = nt.nodes.new("ShaderNodeTexNoise")
        set_in(n, "Scale", scale)
        set_in(n, "Detail", 6.0)
        nt.links.new(coord, n.inputs["Vector"])
        height = n.outputs["Fac"]
    nt.links.new(height, b.inputs["Height"])
    return b.outputs["Normal"]


def principled(name, color, rough=0.5, metal=0.0, sheen=0.0, coat=0.0, bump=0.0, bump_scale=40.0,
               var=0.0, var_scale=3.0, spec=None, transmission=0.0, ior=1.45, alpha=1.0):
    m = new_material(name)
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    set_in(p, "Base Color", (*color, 1.0))
    set_in(p, "Roughness", rough)
    set_in(p, "Metallic", metal)
    set_in(p, "Sheen Weight", sheen)
    set_in(p, "Coat Weight", coat)
    set_in(p, "Transmission Weight", transmission)
    set_in(p, "IOR", ior)
    set_in(p, "Alpha", alpha)
    if spec is not None:
        set_in(p, "Specular IOR Level", spec)
    m.diffuse_color = (*color, alpha)
    if var > 0 or bump > 0:
        coord = _coords(nt)
        if var > 0:
            nt.links.new(_variation(nt, color, var, var_scale, coord), p.inputs["Base Color"])
        if bump > 0:
            nt.links.new(_bump(nt, bump * 0.3, bump_scale, coord), p.inputs["Normal"])
    return m


def _shadow_pass(nt, out, shader, tint):
    """Let shadow rays pass through (light enters through glass without caustic noise)."""
    lp = nt.nodes.new("ShaderNodeLightPath")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    set_in(tr, "Color", (*tint, 1))
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    nt.links.new(shader.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])


def glass(name, tint=(0.96, 0.98, 0.98), rough=0.0):
    m = new_material(name)
    nt, out = clear_nodes(m)
    g = nt.nodes.new("ShaderNodeBsdfPrincipled")
    set_in(g, "Base Color", (*tint, 1))
    set_in(g, "Roughness", rough)
    set_in(g, "Transmission Weight", 1.0)
    set_in(g, "IOR", 1.5)
    _shadow_pass(nt, out, g, tint)
    m.diffuse_color = (*tint, 0.3)
    return m


def water(name, absorb=(0.55, 0.86, 0.92), density=0.5, ripple=0.12, ripple_scale=1.8):
    m = new_material(name)
    nt, out = clear_nodes(m)
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    set_in(p, "Base Color", (*absorb, 1))
    set_in(p, "Roughness", 0.02)
    set_in(p, "Transmission Weight", 1.0)
    set_in(p, "IOR", 1.33)
    coord = _coords(nt)
    w = nt.nodes.new("ShaderNodeTexWave")
    set_in(w, "Scale", ripple_scale)
    set_in(w, "Distortion", 6.0)
    nt.links.new(coord, w.inputs["Vector"])
    nt.links.new(_bump(nt, ripple, ripple_scale, coord, w.outputs["Fac"]), p.inputs["Normal"])
    _shadow_pass(nt, out, p, absorb)
    m.diffuse_color = (*absorb, 1)
    return m


def tiled(name, color, grout, w, h, rough=0.5, var=0.05, grout_w=0.005, offset=0.0, bump=0.2, wall=False):
    """Tiles, pavers or stone courses from the brick texture (tile size w x h metres)."""
    m = new_material(name)
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    set_in(p, "Roughness", rough)
    coord = _coords(nt)
    if wall:
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(coord, sep.inputs[0])
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        add = nt.nodes.new("ShaderNodeMath")
        add.operation = "ADD"
        nt.links.new(sep.outputs["X"], add.inputs[0])
        nt.links.new(sep.outputs["Y"], add.inputs[1])
        nt.links.new(add.outputs[0], comb.inputs["X"])
        nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
        coord = comb.outputs[0]
    br = nt.nodes.new("ShaderNodeTexBrick")
    set_in(br, "Scale", 1.0)
    set_in(br, "Mortar Size", grout_w)
    set_in(br, "Brick Width", w)
    set_in(br, "Row Height", h)
    br.offset = offset
    set_in(br, "Color1", (*color, 1))
    set_in(br, "Color2", (*tuple(c * (1 - var) for c in color), 1))
    set_in(br, "Mortar", (*grout, 1))
    nt.links.new(coord, br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
    if bump > 0:
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(br.outputs["Fac"], inv.inputs[1])
        nt.links.new(_bump(nt, bump * 0.4, 1.0, coord, inv.outputs[0]), p.inputs["Normal"])
    m.diffuse_color = (*color, 1)
    return m


def wood_floor(name, color):
    m = tiled(name, color, tuple(c * 0.55 for c in color), 1.2, 0.18, rough=0.35, var=0.18, grout_w=0.002, offset=0.5, bump=0.15)
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    coord = _coords(nt)
    wv = nt.nodes.new("ShaderNodeTexWave")
    set_in(wv, "Scale", 6.0)
    set_in(wv, "Distortion", 8.0)
    nt.links.new(coord, wv.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    set_in(mix, "Fac", 0.25)
    brick_col = p.inputs["Base Color"].links[0].from_socket
    nt.links.new(brick_col, mix.inputs["Color1"])
    nt.links.new(wv.outputs["Color"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], p.inputs["Base Color"])
    return m


def marble(name, base, vein):
    m = new_material(name)
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    set_in(p, "Roughness", 0.12)
    coord = _coords(nt)
    wv = nt.nodes.new("ShaderNodeTexWave")
    set_in(wv, "Scale", 1.2)
    set_in(wv, "Distortion", 14.0)
    set_in(wv, "Detail", 6.0)
    nt.links.new(coord, wv.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*vein, 1)
    ramp.color_ramp.elements[1].position = 0.18
    ramp.color_ramp.elements[1].color = (*base, 1)
    nt.links.new(wv.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    m.diffuse_color = (*base, 1)
    return m


def leaf_material(name, c1, c2, translucency=0.3):
    m = principled(name, c1, rough=0.75, var=0.0)
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    coord = _coords(nt)
    n = nt.nodes.new("ShaderNodeTexNoise")
    set_in(n, "Scale", 6.0)
    nt.links.new(coord, n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    set_in(p, "Subsurface Weight", translucency * 0.3)
    nt.links.new(_bump(nt, 0.5, 30.0, coord), p.inputs["Normal"])
    return m


def veg_materials():
    if not VEG:
        VEG.update(
            bark=principled("bark", (0.24, 0.21, 0.17), rough=0.9, bump=0.9, bump_scale=18, var=0.2, var_scale=4),
            olive=leaf_material("olive_leaf", (0.16, 0.19, 0.10), (0.42, 0.45, 0.36)),
            cypress=leaf_material("cypress_leaf", (0.03, 0.08, 0.03), (0.06, 0.11, 0.05), translucency=0.2),
            hedge=leaf_material("hedge_leaf", (0.06, 0.13, 0.04), (0.10, 0.18, 0.07), translucency=0.25),
            shrub=leaf_material("shrub_leaf", (0.12, 0.20, 0.07), (0.25, 0.32, 0.18), translucency=0.3),
        )
    return VEG


# ============================================================================ geometry
def _mesh_object(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    if mat is not None:
        me.materials.append(mat)
    link(o)
    return o


def quad(name, a, b, c, d, mat):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in (a, b, c, d)]
    bm.faces.new(vs)
    return _mesh_object(name, bm, mat)


def box(name, x0, x1, y0, y1, z0, z1, mat, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=min(bevel, (x1 - x0) / 3, (y1 - y0) / 3, (z1 - z0) / 3),
                        segments=3, affect="EDGES")
    o = _mesh_object(name, bm, mat)
    for p in o.data.polygons:
        p.use_smooth = bevel > 0
    return o


def cylinder(name, x, y, z, r, h, mat, verts=16):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=h)
    bmesh.ops.translate(bm, vec=(x, y, z + h / 2), verts=bm.verts)
    return _mesh_object(name, bm, mat)


def tube(name, pts, radii, mat, verts=10):
    """Tapered limb through a few points (a cone per segment)."""
    for i in range(len(pts) - 1):
        a, b = Vector(pts[i]), Vector(pts[i + 1])
        d = b - a
        L = d.length
        if L < 1e-6:
            continue
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=radii[i], radius2=radii[i + 1], depth=L)
        rot = d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=bm.verts)
        o = _mesh_object(name, bm, mat)
        for p in o.data.polygons:
            p.use_smooth = True


def blob(name, center, radii, mat, seed=0):
    """Lumpy ellipsoid canopy."""
    rr = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    for v in bm.verts:
        k = 1.0 + rr.uniform(-0.16, 0.16)
        v.co = Vector((v.co.x * radii[0] * k, v.co.y * radii[1] * k, v.co.z * radii[2] * k))
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    o = _mesh_object(name, bm, mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def olive_tree(x, y, s=1.0, seed=0, fast=False, z=-0.05, density=1.0):
    V = veg_materials()
    TREE_POS.append((x, y, s))
    rr = random.Random(seed)
    base = Vector((x, y, z))
    top = base + Vector((rr.uniform(-0.25, 0.25), rr.uniform(-0.25, 0.25), 1.25 * s))
    tube("trunk", [base, base + Vector((0.12, -0.05, 0.55 * s)), top], [0.24 * s, 0.17 * s, 0.13 * s], V["bark"])
    n = rr.choice([3, 4])
    for i in range(n):
        a = 2 * math.pi * i / n + rr.uniform(-0.4, 0.4)
        reach = rr.uniform(0.8, 1.25) * s
        end = top + Vector((math.cos(a) * reach, math.sin(a) * reach, rr.uniform(0.9, 1.5) * s))
        mid = (top + end) / 2 + Vector((0, 0, 0.25 * s))
        tube("limb", [top, mid, end], [0.11 * s, 0.07 * s, 0.035 * s], V["bark"])
        rad = (rr.uniform(1.0, 1.35) * s, rr.uniform(1.0, 1.35) * s, rr.uniform(0.7, 0.95) * s)
        blob("canopy", end + Vector((0, 0, 0.35 * s)), rad, V["olive"], seed * 10 + i)
    blob("canopy_top", top + Vector((0, 0, 2.0 * s)), (1.2 * s, 1.2 * s, 0.85 * s), V["olive"], seed * 10 + 9)


def cypress(x, y, h=7.0, rad=0.6, seed=0, fast=False, z=0.0):
    V = veg_materials()
    cylinder("cypress_trunk", x, y, z, 0.08, 0.6, V["bark"], verts=12)
    blob("cypress", (x, y, z + 0.4 + h / 2), (rad, rad, h / 2), V["cypress"], seed)


def shrub(name, center, radii, kind="hedge", count=None, seed=0, fast=False):
    return blob(name, center, radii, veg_materials()[kind], seed)


# ============================================================================ world, light, camera, render
def daylight(elev, azim, sky=0.05, sun=4.0):
    """Sun at elevation/azimuth (degrees; azimuth clockwise from +Y) and a physical sky."""
    world = bpy.data.worlds.new("world")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    set_in(bg, "Strength", sky * 4.0)
    try:
        sk = nt.nodes.new("ShaderNodeTexSky")
        try:
            sk.sky_type = "NISHITA"
        except Exception:
            pass
        try:
            sk.sun_elevation = math.radians(elev)
            sk.sun_rotation = math.radians(azim)
            sk.sun_disc = False
        except Exception:
            pass
        nt.links.new(sk.outputs["Color"], bg.inputs["Color"])
    except Exception:
        set_in(bg, "Color", (0.55, 0.70, 0.95, 1))
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    ld = bpy.data.lights.new("sun", "SUN")
    ld.energy = sun
    ld.angle = math.radians(1.5)
    so = bpy.data.objects.new("sun", ld)
    link(so)
    az = math.radians(azim)
    d = Vector((math.sin(az) * math.cos(math.radians(elev)), math.cos(az) * math.cos(math.radians(elev)), math.sin(math.radians(elev))))
    so.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    return so


def clouds(coverage=0.4, seed=1.0):
    """Kept for compatibility: the physical sky already gives a soft gradient."""
    return None


def camera(pos, target, lens, shift_y=0.0, two_point=False):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.clip_end = 2000
    co = bpy.data.objects.new("cam", cd)
    link(co)
    p, t = Vector(pos), Vector(target)
    if two_point:
        co.rotation_euler = (math.radians(90), 0.0, math.atan2(t.y - p.y, t.x - p.x) - math.radians(90))
        cd.shift_y = shift_y
    else:
        co.rotation_euler = (t - p).to_track_quat("-Z", "Y").to_euler()
    co.location = p
    bpy.context.scene.camera = co
    return co


def render(out, res="1600x1000", samples=64, exposure=0.0):
    sc = bpy.context.scene
    rx, ry = (int(v) for v in res.split("x"))
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    try:
        sc.cycles.use_denoising = True
    except Exception:
        pass
    sc.cycles.max_bounces = 6
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.resolution_percentage = 100
    for vt in ("AgX", "Filmic"):
        try:
            sc.view_settings.view_transform = vt
            break
        except Exception:
            continue
    for look in ("AgX - Medium High Contrast", "Medium High Contrast", "Filmic - Medium High Contrast"):
        try:
            sc.view_settings.look = look
            break
        except Exception:
            continue
    sc.view_settings.exposure = exposure - 0.6
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


def glb(path, loc=(0, 0, 0), rot_z=0.0, scale=1.0, recolor=None, hide_names=()):
    """Import a glTF binary under an empty; recolor = {material_name_substring: (r, g, b)}."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(os.path.basename(path), None)
    link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
        if any(h in o.name for h in hide_names):
            o.hide_render = True
    if recolor:
        for o in new:
            for slot in getattr(o, "material_slots", []):
                m = slot.material
                if m is None:
                    continue
                for key, col in recolor.items():
                    if key in m.name and m.use_nodes:
                        p = m.node_tree.nodes.get("Principled BSDF")
                        if p is not None:
                            set_in(p, "Base Color", (*col, 1))
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    root.scale = (scale, scale, scale)
    return root
