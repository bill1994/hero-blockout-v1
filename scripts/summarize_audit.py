"""Summarize the two audit JSONs into a compact readable survey."""
import json
import os

A = r"G:\DSHProject\BlenderMcp\audit"
p19 = json.load(open(os.path.join(A, "p19_bind.json"), encoding="utf-8"))
tri = json.load(open(os.path.join(A, "tripo_parts.json"), encoding="utf-8"))

acts = {a["name"]: a for a in p19["actions"]}
anim = [o for o in p19["objects"] if o["action"]]

print("=" * 78)
print("P19  objects=%d  actions=%d  animated=%d  frames=%s  fps=%s  cam=%s" % (
    p19["n_objects"], p19["n_actions"], len(anim),
    p19["scene_frame_range"], p19["fps"], p19["active_camera"]))
print("=" * 78)

print("\n-- A. animated object -> action -> slot -> frame range --")
for o in sorted(anim, key=lambda x: x["name"]):
    a = acts.get(o["action"], {})
    print("%-24s %-6s %-30s slot=%-10s fr=%s  paths=%d" % (
        o["name"], o["type"], o["action"], str(o["action_slot"]),
        a.get("frame_range"), a.get("n_fcurves", 0)))

used = {o["action"] for o in anim}
print("\n-- B. actions NOT attached to any object (V1 leftovers etc.) --")
for n in sorted(acts):
    if n not in used:
        a = acts[n]
        print("%-32s users=%-3d fr=%s  paths=%s" % (
            n, a["users"], a["frame_range"], a["paths"][:3]))

print("\n-- C. arm pivot world positions --")
for o in p19["objects"]:
    nm = o["name"]
    if nm.startswith("Arm_") and any(k in nm for k in ("Pivot", "Base", "Wrist", "Mount", "Yaw")):
        print("%-22s %-6s world=%-34s parent=%s" % (
            nm, o["type"], str(o["world_loc"]), o["parent"]))

print("\n-- D. machine/legacy object world locations --")
for o in p19["objects"]:
    nm = o["name"]
    if nm.startswith(("Machine_", "Product", "Prop_")) and o["type"] != "EMPTY" or nm in ("Machine_Root",):
        if o["type"] in ("MESH", "EMPTY"):
            print("%-24s %-6s world=%-34s dim=%s parent=%s" % (
                nm, o["type"], str(o["world_loc"]), str(o["dimensions"]), o["parent"]))

print("\n" + "=" * 78)
print("TRIPO  parts=%d  tris=%d  verts=%d" % (
    tri["n_parts"], tri["total_tris"], tri["total_verts"]))
print("=" * 78)
print("%-18s %5s %6s  %-22s %-26s %s" % ("part", "tris", "maxdim", "center(x,y,z)", "size(x,y,z)", "mat"))
for p in tri["parts"]:
    print("%-18s %5d %6.3f  %-22s %-26s %s" % (
        p["name"], p["tris"], p["max_dim"],
        "%.3f,%.3f,%.3f" % tuple(p["center"]),
        "%.3f,%.3f,%.3f" % tuple(p["size"]),
        p["mats"][0] if p["mats"] else "-"))
