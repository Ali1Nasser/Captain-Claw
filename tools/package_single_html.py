from pathlib import Path
import base64, gzip, sys

if len(sys.argv) != 3:
    raise SystemExit("usage: package_single_html.py <web-build-dir> <output.html>")
root=Path(sys.argv[1]); out=Path(sys.argv[2])
engine=(root/'openclaw.js').read_text(encoding='utf-8')
if '</script' in engine.lower():
    raise RuntimeError('Generated openclaw.js unexpectedly contains </script>')
data_gz=gzip.compress((root/'openclaw.data').read_bytes(), compresslevel=9, mtime=0)
wasm_gz=gzip.compress((root/'openclaw.wasm').read_bytes(), compresslevel=9, mtime=0)
data_b64=base64.b64encode(data_gz).decode('ascii')
wasm_b64=base64.b64encode(wasm_gz).decode('ascii')
head=r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="theme-color" content="#050505"><title>OpenClaw v1.03 — Full Real Mobile</title>
<style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#000;color:#fff;font-family:Arial,Helvetica,sans-serif;touch-action:none;overscroll-behavior:none;-webkit-user-select:none;user-select:none}
#gameShell{position:fixed;inset:0;background:#000;display:flex;align-items:center;justify-content:center}
#canvas{display:block;width:100vw;height:100dvh;object-fit:contain;background:#000;outline:0}
#boot{position:fixed;inset:0;z-index:1000;background:radial-gradient(circle at 50% 35%,#33220c 0,#130d08 30%,#030303 72%);display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box}
#boot.hidden{display:none}
#panel{width:min(720px,94vw);text-align:center;background:rgba(0,0,0,.72);border:1px solid rgba(255,188,70,.38);border-radius:20px;padding:26px;box-shadow:0 12px 60px #000}
#title{font-size:clamp(28px,6vw,56px);font-weight:900;letter-spacing:.04em;color:#f5b53a;text-shadow:0 2px 0 #5d3200;margin:0 0 8px}
#subtitle{font-size:14px;opacity:.78;margin-bottom:20px}
#status{font-size:16px;min-height:24px;margin:12px 0;color:#fff}
#bar{height:12px;border-radius:8px;background:#24180b;overflow:hidden;border:1px solid #6f4b19}
#fill{height:100%;width:0;background:linear-gradient(90deg,#b76a14,#ffd066);transition:width .15s linear}
#detail{margin-top:10px;font-size:12px;opacity:.62;min-height:18px;word-break:break-word}
#start{font-size:22px;font-weight:800;padding:14px 30px;border:2px solid #ffd36b;border-radius:14px;background:linear-gradient(#d78b22,#864810);color:#fff;text-shadow:0 1px 2px #000;box-shadow:0 6px 24px #000;cursor:pointer}
#start:disabled{opacity:.45}
#topTools{position:fixed;z-index:900;right:max(10px,env(safe-area-inset-right));top:max(10px,env(safe-area-inset-top));display:flex;gap:8px}
.tool{border:1px solid rgba(255,255,255,.35);background:rgba(0,0,0,.58);color:white;border-radius:11px;padding:10px 13px;font-weight:700;font-size:14px}
#errorBox{display:none;white-space:pre-wrap;text-align:left;background:#260606;border:1px solid #ad3333;border-radius:10px;padding:12px;margin-top:12px;max-height:30vh;overflow:auto;font:12px/1.4 monospace}
@media (orientation:portrait){#panel:after{content:'Rotate your phone to landscape for the best experience.';display:block;margin-top:14px;color:#ffd36b;font-size:13px}}
</style></head><body>
<div id="gameShell"><canvas id="canvas" width="1600" height="900" tabindex="-1" oncontextmenu="event.preventDefault()"></canvas></div>
<div id="topTools"><button class="tool" id="fsBtn">⛶ Fullscreen</button></div>
<div id="boot"><div id="panel"><div id="title">OPENCLAW</div><div id="subtitle">Real pjasicek/OpenClaw engine • Official v1.03 resources • Single-file mobile build</div><button id="start">START CAPTAIN CLAW</button><div id="status">Tap Start to unpack the embedded real game.</div><div id="bar"><div id="fill"></div></div><div id="detail">No internet or companion files are required.</div><div id="errorBox"></div></div></div>
<script>
(function(){
'use strict';
const bootEl=document.getElementById('boot'), statusEl=document.getElementById('status'), fillEl=document.getElementById('fill'), detailEl=document.getElementById('detail'), errorEl=document.getElementById('errorBox'), startBtn=document.getElementById('start'), canvas=document.getElementById('canvas');
let failed=false;
function status(t,p,d){statusEl.textContent=t;if(Number.isFinite(p))fillEl.style.width=Math.max(0,Math.min(100,p))+'%';if(d!==undefined)detailEl.textContent=d;}
function fail(e){failed=true;const msg=(e&&e.stack)||String(e);console.error(e);statusEl.textContent='OpenClaw could not start';fillEl.style.width='100%';fillEl.style.background='#b32323';detailEl.textContent='The exact startup error is shown below.';errorEl.style.display='block';errorEl.textContent=msg;startBtn.disabled=false;startBtn.textContent='RETRY';}
window.addEventListener('error',e=>{if(!failed)fail(e.error||e.message)});
window.addEventListener('unhandledrejection',e=>{if(!failed)fail(e.reason||e)});
async function enterFullscreen(){try{if(!document.fullscreenElement&&document.documentElement.requestFullscreen)await document.documentElement.requestFullscreen({navigationUI:'hide'});}catch(_){ }try{if(screen.orientation&&screen.orientation.lock)await screen.orientation.lock('landscape');}catch(_){ }}
document.getElementById('fsBtn').addEventListener('click',enterFullscreen);
function base64GzipToArrayBuffer(textEl,label,p0,p1){
 return new Promise(async(resolve,reject)=>{
  try{
   if(typeof DecompressionStream==='undefined') throw new Error('This Chrome version does not provide DecompressionStream. Update Chrome and try again.');
   let text=textEl.textContent, pos=0, chunkChars=1024*1024;
   const total=text.length;
   const compressedStream=new ReadableStream({pull(controller){
     if(pos>=total){controller.close();textEl.remove();return;}
     let end=Math.min(total,pos+chunkChars);end-=((end-pos)%4);if(end<=pos)end=total;
     const part=text.slice(pos,end);pos=end;
     const bin=atob(part);const bytes=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
     controller.enqueue(bytes);
     const q=pos/total;status('Unpacking '+label+'…',p0+(p1-p0)*q,Math.round(q*100)+'% of embedded '+label+' decoded');
   }});
   const decompressed=compressedStream.pipeThrough(new DecompressionStream('gzip'));
   const buf=await new Response(decompressed).arrayBuffer();
   text=null;resolve(buf);
  }catch(e){reject(e)}
 });
}
async function bootGame(){
 failed=false;startBtn.disabled=true;startBtn.style.display='none';errorEl.style.display='none';
 enterFullscreen();
 try{
  status('Preparing real Captain Claw game data…',2,'This first start can take a little while because the game is fully embedded.');
  const dataBuffer=await base64GzipToArrayBuffer(document.getElementById('ocData'),'game data',3,58);
  status('Preparing OpenClaw WebAssembly engine…',60,(dataBuffer.byteLength/1048576).toFixed(1)+' MB game package ready');
  const wasmBuffer=await base64GzipToArrayBuffer(document.getElementById('ocWasm'),'engine',60,78);
  status('Starting the real OpenClaw engine…',80,(wasmBuffer.byteLength/1048576).toFixed(1)+' MB WebAssembly engine ready');
  let preload=dataBuffer;
  window.Module={
    canvas:canvas,
    preRun:[],
    wasmBinary:new Uint8Array(wasmBuffer),
    getPreloadedPackage:function(name,size){
      if(String(name).indexOf('openclaw.data')!==-1&&preload){const b=preload;preload=null;status('Loading original Captain Claw resources…',84,'Creating the OpenClaw virtual filesystem');return b;}
      return null;
    },
    setStatus:function(t){if(!t)return;let p=86;if(/running|ready/i.test(t))p=97;status(t,p,'OpenClaw engine startup');},
    print:function(){console.log.apply(console,arguments)},
    printErr:function(){console.error.apply(console,arguments)},
    onRuntimeInitialized:function(){status('OpenClaw engine ready',98,'Launching Captain Claw…');canvas.focus();setTimeout(()=>{bootEl.classList.add('hidden');},400)},
    onAbort:function(reason){fail(new Error('OpenClaw aborted: '+reason))}
  };
  const src=document.getElementById('ocEngine').textContent;
  document.getElementById('ocEngine').remove();
  const s=document.createElement('script');s.text=src+'\n//# sourceURL=openclaw-inline.js';document.body.appendChild(s);
 }catch(e){fail(e)}
}
startBtn.addEventListener('click',bootGame,{passive:true});
status('Ready',0,'Tap START CAPTAIN CLAW. The first load unpacks the embedded real game into memory.');
})();
</script>
"""
middle='\n<script type="application/octet-stream" id="ocData">'+data_b64+'</script>\n<script type="application/octet-stream" id="ocWasm">'+wasm_b64+'</script>\n'
tail='\n<script type="text/plain" id="ocEngine">'+engine+'</script>\n</body></html>\n'
out.write_text(head+middle+tail,encoding='utf-8')
print(f"Created {out} ({out.stat().st_size} bytes; compressed data {len(data_gz)}; compressed wasm {len(wasm_gz)})")
