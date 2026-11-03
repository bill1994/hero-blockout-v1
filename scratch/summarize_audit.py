import json, sys, re
raw = open('scratch/audit_deep.json', encoding='utf-8').read()
raw = raw.split('###JSON_START###')[1].split('###JSON_END###')[0]
D = json.loads(raw)

print("="*70); print("SCENE:", D.get('total_tris'), "tris (visible)")

print("\n"+"="*70); print("1) BASE")
for n,d in D['BASE'].items():
    if d.get('missing'): continue
    print(f"  {n}: dim={d['dim']} bbox_min={d['bbox_min']} bbox_max={d['bbox_max']}")
    print(f"      parent={d['parent']} scale={d['scale']} rot={d['rot_deg']}")
    print(f"      mods={[(m['name'],m['type'],m.get('width'),m.get('segments')) for m in d['modifiers']]}")
    print(f"      mats={d['materials']} mesh={d.get('mesh')}")
print("\n  BASE profile slices:")
for p in D.get('BASE_profile',[]): print("   ", p)

print("\n"+"="*70); print("2) BOLTS")
print("  positions:")
for n,p in D['BOLTS_positions'].items():
    print(f"   {n}: world={p['world']} rot={p['rot_deg']} v={p['verts']} f={p['polys']} mat={p['mat']}")
print("\n  boolean modifiers in scene:")
for b in D.get('BOOLEANS',[]): print("   ", b)
print("\n  bolt detail:")
for n,d in D['BOLTS'].items():
    if d.get('missing'): continue
    print(f"   {n}: dim={d['dim']} mods={[(m['name'],m['type'],m.get('width')) for m in d['modifiers']]} mesh={d.get('mesh')}")

print("\n"+"="*70); print("3) CLAW")
for n,d in D['CLAW'].items():
    if d.get('missing'): continue
    print(f"  {n}: dim={d['dim']} bbox_min={d['bbox_min']} bbox_max={d['bbox_max']}")
    print(f"      parent={d['parent']} scale={d['scale']} rot={d['rot_deg']}")
    print(f"      mods={[(m['name'],m['type'],m.get('width'),m.get('segments')) for m in d['modifiers']]}")
    print(f"      mats={d['materials']} mesh={d.get('mesh')}")
for fr,fg in D.get('CLAW_by_frame',{}).items():
    print(f"\n  --- {fr} ---")
    for n,v in fg.items():
        print(f"   {n}: dim={v['dim']} centre={v['world_centre']} rot={v['rot_deg']} scale={v['scale']}")
for fr,rs in D.get('CLAW_radial',{}).items():
    print(f"\n  radial {fr}:")
    for r in rs: print("   ", r)

print("\n"+"="*70); print("4) OUTLET")
for n,d in D['OUTLET'].items():
    if d.get('missing'): continue
    print(f"  {n}: dim={d['dim']} bbox_min={d['bbox_min']} bbox_max={d['bbox_max']}")
    print(f"      parent={d['parent']} hide_render={d['hide_render']} visible={d['visible']}")
    print(f"      mods={[(m['name'],m['type'],m.get('width'),m.get('segments'),m.get('operation'),m.get('target')) for m in d['modifiers']]}")
    print(f"      mats={d['materials']} mesh={d.get('mesh')}")
print("\n  CHUTE openness:", D.get('CHUTE_openness'))
print("\n  CHUTE slices (y,z) at x:")
for x,pts in D.get('CHUTE_slices',{}).items():
    print(f"   x={x}: n={len(pts)}")
    if pts: print(f"      y {pts[0][0]} .. {pts[-1][0]}   z {min(p[1] for p in pts)} .. {max(p[1] for p in pts)}")
print("\n  AXIS RAYS (+X from inside body):")
for z,r in D.get('AXIS_RAYS',{}).items():
    print(f"   {z}: {r}")
