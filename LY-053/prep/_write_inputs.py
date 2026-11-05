# helper: writes inputs.json (run with python -I from prep/)
import json
B = 'D:/GitHub/creation-notebook-lab/'
K = B + 'docs/library/models/m-luoyang-tile-kiln/'
MQ = 'C:/Users/suxin/AppData/Local/Temp/claude/bfd0867865ae17cc/14ddfcf2-ca06-49dc-95f8-4586da1502c1/scratchpad/mq/'
notcity = 'not referenced in docs/cities/luoyang/city-data.mjs (grep kiln/窑: 0 hits); shown only via the library asset card'
inputs = {
    "seat": "LY-053", "phase": "prep (G not frozen; no delivery geometry produced)",
    "baseline": {"repo": B, "commit": "bce3211f818ee5a8bef1773539da70695ba37b17",
                 "note": "kiln files: git blob == HEAD; lab/data/assets.json, glb-cache.json, report.json are modified in the lab worktree (not by this seat)"},
    "axis": "Measured in Blender 5.2.1 after glTF import: Z-up, glTF +Y -> +Z, glTF +Z -> -Y, metres, kiln-local origin. Final convention per LY-005.",
    "inputs": [
        {"id": "kiln-A-LOD0", "path": K + "files/kiln-A.glb", "sha256": "e67d597617c3cdeb5d611f233438fa529151afddbc73ad9a2a98315cc9252f01", "bytes": 1208676, "gitBlob": "f79eb8a7615b", "loadedInCity": False, "loadedBy": notcity, "role": "kiln body, mutex variant A; drop node A_presentation_ground"},
        {"id": "kiln-B-LOD0", "path": K + "files/kiln-B.glb", "sha256": "4886d95d22383a9b26870d36b476f2efa3b35fe68037df6b444847fd38980d91", "bytes": 1207668, "gitBlob": "b8d3dea39dc7", "loadedInCity": False, "loadedBy": notcity, "role": "kiln body, mutex variant B; drop node B_presentation_ground"},
        {"id": "kiln-A-LOD1", "path": K + "files/kiln-A-LOD1.glb", "sha256": "562b4b398bb97ea4478f0d6e06595994b16725139ee9e80ad66c28501efb69c9", "bytes": 821880, "gitBlob": "6c02cf700178", "loadedInCity": False, "loadedBy": notcity, "role": "LOD1 of A; still contains A_presentation_ground"},
        {"id": "kiln-B-LOD1", "path": K + "files/kiln-B-LOD1.glb", "sha256": "8d9db85bf26e911ffca14123784f97f5b0c7677cf2cce8cf762d8dc21167a0d5", "bytes": 820856, "gitBlob": "90c8861726af", "loadedInCity": False, "loadedBy": notcity, "role": "LOD1 of B; still contains B_presentation_ground"},
        {"id": "kiln-card", "path": K + "m-luoyang-tile-kiln.asset.json", "sha256": "99f6320539659444c3317a2245378ea3215ce5e96f586159b08ace696f8311f5", "loadedInCity": False, "role": "status 待审; limits note says display ground and pit need re-fitting"},
        {"id": "kiln-cover", "path": K + "cover.webp", "sha256": "f3e3bfceb53851c87604f90c7afbd953c3aae5ed9557dd4169c31553251dbacc", "loadedInCity": False, "role": "CPU preview only"},
        {"id": "kiln-shot-01", "path": K + "shots/01.webp", "sha256": "4eb104a70f4ab45cf48f7901558b24c627dff543dfea25aedd89b5d1d7899953", "loadedInCity": False},
        {"id": "kiln-shot-02", "path": K + "shots/02.webp", "sha256": "2cc6bb2c818d79e78f414dd60f3d66466c8b4ae8df4f5627a29a6a4e2fbdb0b7", "loadedInCity": False},
        {"id": "city-data", "path": B + "docs/cities/luoyang/city-data.mjs", "sha256": "e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a", "loadedInCity": True, "loadedBy": "city app data module", "role": "evidence that no kiln record exists; read only, LY-100 owns"},
        {"id": "city-renderer", "path": B + "docs/cities/luoyang/city-renderer.mjs", "sha256": "fa0a8dcbfaa5f5f8bd410f3d2295d788f32480c4dab316dd291a561d40d026ca", "loadedInCity": True, "loadedBy": "city-renderer.mjs:309 builds the excluded-node set from asset.excludeNodes || asset.removable_site_nodes", "role": "existing mechanism to drop <V>_presentation_ground at load without editing the GLB"},
        {"id": "ground-atomic-check", "path": B + "docs/cities/luoyang/v1/ground-atomic.mjs", "sha256": "45e25711f8a1e98db6751d2644f6fe5ca127e7798b60eb85eb9666db794380b0", "loadedInCity": True, "loadedBy": "v1/road-layer.mjs:19 and v1/west-layer.mjs:40 call assertGroundAtomic", "role": "only checks the 3 required nodes appear exactly once; no cut/hole support"},
        {"id": "ground-atomic-contract", "path": B + "docs/cities/luoyang/data/west/ground-atomic-contract.json", "sha256": "bfc7fc83c3d8f34c79e9395532b74c324987b4dbf0c4342328b7581ebc2be584", "loadedInCity": True, "loadedBy": "fetched in v1/road-layer.mjs:19 and v1/west-layer.mjs:40; cited by city-data.mjs ground-* records", "role": "template for the LY-053 atomic cut contract (atomic, allNodesRequired, replaceResources, keep)"},
        {"id": "ground-network-stitched", "path": B + "docs/cities/luoyang/assets/ground-atomic/network-ground-stitched.glb", "sha256": "fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60", "loadedInCity": True, "loadedBy": "city-data.mjs asset ground-network-ground-stitched (bounds y 0..0.21)", "role": "possible future host ground; no host tile designated (no site admission)"},
        {"id": "project-card", "path": B + "docs/cities/luoyang/p-luoyang.asset.json", "sha256": "9b5e311f077aa6c2fb433ba36cca6dc291542848769134335418a558b92b089d", "loadedInCity": False, "role": "lists 砖瓦窑 A/B as 已建模 / 未入城 (line ~240) and related id (line 543)"},
        {"id": "lab-assets-json", "path": B + "lab/data/assets.json", "sha256_HEAD": "53d863121bb583b362bf9929bf18c1d91aaf6f36fb8d3808e70a8a3e4825df78", "sha256_worktree": "3440caa2a38a0893e4c27177c0127fc46ea6ffec31694ab3c1d6980d212c3f7a", "loadedInCity": False, "role": "summary; worktree differs from HEAD (not this seat)"},
        {"id": "mq-audit", "path": MQ + "cards/m-luoyang-tile-kiln/audit.json", "sha256": "cabc9607d0a2b2992c0c58dd14e4e8a25b86ef2a6a393b6d33bf2a85de26cfc6", "role": "prior audit: 0 issues; bbox 16 x 3.54 x 19 includes the display ground"},
        {"id": "mq-render", "path": MQ + "render.py", "sha256": "ff89761743a064f7d599835e3e3123f330ca152df43634717c312ece667d4dc7", "role": "unified CPU workbench render for previews"},
    ],
    "missing": [
        {"id": "kiln-native-source", "what": ".blend / generator / source ZIP for m-luoyang-tile-kiln",
         "searched": "D:/GitHub depth 6 for *kiln*: only docs/media copies; git log --all on *kiln*: only 52fceaa",
         "use": "re-export the kiln without the display ground; parametric pit sizes",
         "rebuildFromGLB": "yes / not required: kiln stays read-only, display ground dropped by excludeNodes; pit and base parts are axis-aligned boxes reconstructable from measured planes"},
        {"id": "G-pack", "what": "frozen LY-005 axes/ports, LY-006 ownership, LY-007 material/LOD baseline, LY-008 checker, LY-010 admission",
         "use": "port IDs, material names, checker entry, whether any site may host a pit", "rebuildFromGLB": "no"},
        {"id": "site-admission", "what": "real kiln-yard location (LY-010 / LY-003)", "use": "host ground tile for the atomic cut", "rebuildFromGLB": "no; cut contract keeps host=null"},
        {"id": "primary-evidence", "what": "excavation report of an Eastern Han Luoyang brick/tile kiln with pit depth and plan", "use": "evidence column; all current numbers are C", "rebuildFromGLB": "no"},
    ],
}
sha = {}
import hashlib, os
for f in sorted(os.listdir('.')):
    if f.endswith(('.py', '.json')) and f not in ('inputs.json', 'prep-status.json', '_write_inputs.py'):
        sha[f] = hashlib.sha256(open(f, 'rb').read()).hexdigest()
inputs["prepFiles"] = sha
json.dump(inputs, open('inputs.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', len(sha))
