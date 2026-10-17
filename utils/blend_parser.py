import subprocess, json, tempfile, os

def _run_script(blender_exe, blend_path, script):
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(script)
            tmp = f.name
        try:
            r = subprocess.run([blender_exe, "-b", blend_path, "--python-exit-code", "1", "--python", tmp],
                               capture_output=True, text=True, timeout=120)
            return (r.stdout + r.stderr)
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass
    except Exception as e:
        return str(e)

def list_scenes(blender_exe, blend_path):
    script = "import bpy,json; print('SCENES:'+json.dumps([s.name for s in bpy.data.scenes]))"
    out = _run_script(blender_exe, blend_path, script)
    for line in out.splitlines():
        if line.startswith("SCENES:"):
            return json.loads(line[len("SCENES:"):])
    return []

def list_cameras(blender_exe, blend_path, scene_name=None):
    scn = f"bpy.data.scenes['{scene_name}']" if scene_name else "bpy.context.scene"
    script = (
        "import bpy,json; s=%s; cams=[o.name for o in s.objects if o.type=='CAMERA']; "
        "print('CAMERAS:'+json.dumps(cams))" % scn
    )
    out = _run_script(blender_exe, blend_path, script)
    for line in out.splitlines():
        if line.startswith("CAMERAS:"):
            try:
                return json.loads(line[len("CAMERAS:"):])
            except Exception:
                return []
    return []

def list_compositors(blender_exe, blend_path, scene_name=None):
    script = (
        "import bpy,json; names=[g.name for g in bpy.data.node_groups]; "
        "print('COMPS:'+json.dumps(names))"
    )
    out = _run_script(blender_exe, blend_path, script)
    for line in out.splitlines():
        if line.startswith("COMPS:"):
            try:
                return json.loads(line[len("COMPS:"):])
            except Exception:
                return []
    return []

def microscript_set_camera(camera):
    return "import bpy; bpy.context.scene.camera=bpy.data.objects.get(%r)" % camera
