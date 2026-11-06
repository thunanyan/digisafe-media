#!/usr/bin/env python3
"""Render a DigiSafe feed post (1080x1080) or story (1080x1920) from a JSON spec.

Usage: python3 tools/render.py spec.json [outdir]
Spec: {"kind":"post"|"story","headline":"...","accent":"key words in yellow","body":"...",
       "badges":["..",".."],"name":"output-file-name-without-extension"}
Writes <name>.png and <name>.jpg into outdir (default ./out).
Needs: google-chrome, node/npm (for Armenian fonts), python3 with Pillow.
"""
import json, os, subprocess, sys, shutil, html, pathlib
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE / "assets"
PHONE = "+37412585999"

def ensure_fonts(work):
    if not (work / "node_modules/@fontsource/noto-serif-armenian").exists():
        subprocess.run(["npm", "install", "--silent", "--prefix", str(work),
                        "@fontsource/noto-serif-armenian", "@fontsource/noto-sans-armenian"], check=True)

def page(spec):
    kind = spec["kind"]
    story = kind == "story"
    W, H = 1080, 1920 if story else 1080
    h = html.escape(spec["headline"]); a = html.escape(spec.get("accent", ""))
    body = html.escape(spec.get("body", ""))
    badges = "".join(
        f'<div class="b">{html.escape(b)}</div>' for b in spec.get("badges", []))
    pad = "240px 72px 300px 72px" if story else "72px"
    hs = 124 if story else 112
    bs = 42 if story else 34
    bb = 32 if story else 24
    logo_w = 700 if story else 620
    badge_h = 110 if story else 84
    ring = ('<div class="r" style="right:-300px;top:520px;width:900px;height:900px;opacity:.3"></div>'
            '<div class="r" style="right:-180px;top:640px;width:660px;height:660px;opacity:.5"></div>'
            '<div class="r" style="right:-60px;top:760px;width:420px;height:420px"></div>') if story else (
            '<div class="r" style="right:-220px;top:120px;width:760px;height:760px;opacity:.35"></div>'
            '<div class="r" style="right:-120px;top:220px;width:560px;height:560px;opacity:.55"></div>'
            '<div class="r" style="right:-20px;top:320px;width:360px;height:360px"></div>')
    return f"""<!doctype html><html lang="hy"><head><meta charset="utf-8"><style>
@font-face{{font-family:'NSA';font-weight:800;src:url('node_modules/@fontsource/noto-serif-armenian/files/noto-serif-armenian-armenian-800-normal.woff2') format('woff2');}}
@font-face{{font-family:'NSSA';font-weight:400;src:url('node_modules/@fontsource/noto-sans-armenian/files/noto-sans-armenian-armenian-400-normal.woff2') format('woff2');}}
@font-face{{font-family:'NSSA';font-weight:600;src:url('node_modules/@fontsource/noto-sans-armenian/files/noto-sans-armenian-armenian-600-normal.woff2') format('woff2');}}
@font-face{{font-family:'NSSA';font-weight:700;src:url('node_modules/@fontsource/noto-sans-armenian/files/noto-sans-armenian-armenian-700-normal.woff2') format('woff2');}}
body{{margin:0}}
.c{{position:relative;width:{W}px;height:{H}px;box-sizing:border-box;padding:{pad};background:#0F3B2A;color:#E4EFD3;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between;font-family:'NSSA',system-ui,sans-serif}}
.r{{position:absolute;border-radius:50%;border:3px solid #F8DC24}}
h1{{margin:0;font-family:'NSA',Georgia,serif;font-weight:800;font-size:{hs}px;line-height:1.1;color:#7BEA6A}}
h1 span{{color:#F8DC24}}
p{{margin:0;font-size:{bs}px;line-height:1.5;color:#CFE3B4;max-width:{860 if story else 760}px}}
.bw{{display:flex;{'flex-direction:column;align-items:flex-start;' if story else 'flex-wrap:wrap;'}gap:16px}}
.b{{padding:14px 28px;border:3px solid #F8DC24;border-radius:999px;font-size:{bb}px;font-weight:600}}
.f{{display:flex;flex-direction:column;gap:20px;border-top:3px solid #2F6B52;padding-top:28px}}
.ph{{font-size:{38 if story else 30}px;font-weight:700;color:#F8DC24}}
.st{{display:flex;gap:16px}}
.st img{{height:{badge_h}px;width:auto;border-radius:12px;background:#fff}}
</style></head><body><div class="c">{ring}
<div style="position:relative"><img src="assets/logo.png" style="width:{logo_w}px;height:auto;display:block"></div>
<div style="position:relative;display:flex;flex-direction:column;gap:{36 if story else 28}px">
<h1>{h} <span>{a}</span></h1><p>{body}</p><div class="bw">{badges}</div></div>
<div class="f" style="position:relative"><div class="ph">{PHONE}</div>
<div class="st"><img src="assets/appstore.png"><img src="assets/googleplay.png"></div></div>
</div><script>document.fonts.ready.then(function(){{var c=document.querySelector('.c'),h=document.querySelector('h1'),s=parseFloat(getComputedStyle(h).fontSize);while(c.scrollHeight>c.clientHeight+1&&s>48){{s-=4;h.style.fontSize=s+'px';}}}});</script></body></html>"""

def main():
    spec = json.load(open(sys.argv[1]))
    out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "out"); out.mkdir(parents=True, exist_ok=True)
    work = pathlib.Path(os.environ.get("DIGISAFE_RENDER_WORK", "/tmp/digisafe-render")); work.mkdir(parents=True, exist_ok=True)
    ensure_fonts(work)
    shutil.copytree(ASSETS, work / "assets", dirs_exist_ok=True)
    (work / "page.html").write_text(page(spec), encoding="utf-8")
    w, h = (1080, 1920) if spec["kind"] == "story" else (1080, 1080)
    png = out / (spec["name"] + ".png")
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--virtual-time-budget=4000", f"--window-size={w},{h}", f"--screenshot={png}",
                    f"file://{work}/page.html"], check=True, capture_output=True)
    Image.open(png).convert("RGB").save(out / (spec["name"] + ".jpg"), quality=92)
    print(png, out / (spec["name"] + ".jpg"))

main()
