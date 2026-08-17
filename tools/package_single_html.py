from pathlib import Path
import base64
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: package_single_html.py <web-build-dir> <output.html>")

root = Path(sys.argv[1])
out = Path(sys.argv[2])
html = (root / "openclaw.html").read_text(encoding="utf-8")
js = (root / "openclaw.js").read_text(encoding="utf-8")

html = html.replace(
    '<meta name="viewport" content="width=660">',
    '<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">',
)

html = html.replace(
    "</style>",
    """
        html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#000;touch-action:none;overscroll-behavior:none;-webkit-user-select:none;user-select:none}
        body{position:fixed;inset:0;display:flex;align-items:center;justify-content:center}
        body>div:first-of-type{margin:0!important;width:100vw;height:100dvh;display:flex;align-items:center;justify-content:center;background:#000}
        #canvas{display:block;max-width:100vw;max-height:100dvh;width:auto;height:auto;outline:none;image-rendering:auto;touch-action:none}
        body>div:nth-of-type(2){position:fixed;left:max(8px,env(safe-area-inset-left));top:max(8px,env(safe-area-inset-top));z-index:50;margin:0;background:rgba(0,0,0,.45);padding:5px;border-radius:8px;color:#fff;font-family:Arial,sans-serif;font-size:11px;opacity:.28;transition:opacity .2s}
        body>div:nth-of-type(2):hover,body>div:nth-of-type(2):active{opacity:1}
        body>div:nth-of-type(2) label,body>div:nth-of-type(2) select{display:none}
        body>div:nth-of-type(2) button{padding:6px 10px;font-size:11px}
        #loading{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;color:white;background:#000;font:700 18px Arial,sans-serif;text-align:center;padding:24px;z-index:100}
    </style>""",
)

marker = "    loadGame();\n"
if marker not in html:
    marker = "\tloadGame();\r\n"
if marker not in html:
    raise RuntimeError("Could not locate loadGame() execution point in generated shell")
pre, post = html.split(marker, 1)

bootstrap = """    // Standalone packaging for the genuine generated Emscripten binaries.
    function __ocDecodeBase64(b64) {
        var padding = b64.endsWith('==') ? 2 : (b64.endsWith('=') ? 1 : 0);
        var total = Math.floor(b64.length * 3 / 4) - padding;
        var out = new Uint8Array(total);
        var outPos = 0;
        var CHUNK = 4 * 1024 * 1024;
        for (var i = 0; i < b64.length; i += CHUNK) {
            var bin = atob(b64.slice(i, Math.min(i + CHUNK, b64.length)));
            for (var j = 0; j < bin.length; j++) out[outPos++] = bin.charCodeAt(j);
        }
        return out;
    }
    var __ocDataB64 = '"""

between = """';
    var __ocWasmB64 = '"""

after = """';
    Module.getPreloadedPackage = function(name, size) {
        if (String(name).indexOf('openclaw.data') !== -1 && __ocDataB64) {
            if (loadingElement) loadingElement.innerHTML = 'Preparing embedded Captain Claw game data...';
            var bytes = __ocDecodeBase64(__ocDataB64);
            __ocDataB64 = null;
            return bytes.buffer;
        }
        return null;
    };
    if (loadingElement) loadingElement.innerHTML = 'Preparing embedded OpenClaw engine...';
    Module.wasmBinary = __ocDecodeBase64(__ocWasmB64);
    __ocWasmB64 = null;

"""

def write_b64(dst, src_path):
    with open(src_path, "rb") as src:
        carry = b""
        while True:
            chunk = src.read(3 * 1024 * 1024)
            if not chunk:
                break
            chunk = carry + chunk
            n = (len(chunk) // 3) * 3
            body, carry = chunk[:n], chunk[n:]
            if body:
                dst.write(base64.b64encode(body))
        if carry:
            dst.write(base64.b64encode(carry))

with out.open("wb") as f:
    f.write(pre.encode("utf-8"))
    f.write(bootstrap.encode("utf-8"))
    write_b64(f, root / "openclaw.data")
    f.write(between.encode("utf-8"))
    write_b64(f, root / "openclaw.wasm")
    f.write(after.encode("utf-8"))
    f.write(js.encode("utf-8"))
    f.write(b"\n")
    f.write(post.encode("utf-8"))

print(f"Created {out} ({out.stat().st_size} bytes)")
