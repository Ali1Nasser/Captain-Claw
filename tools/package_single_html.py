from pathlib import Path
import base64, gzip, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: package_single_html.py <web-build-dir> <output.html>')
root=Path(sys.argv[1]); out=Path(sys.argv[2])
engine=(root/'openclaw.js').read_text(encoding='utf-8')
data_gz=gzip.compress((root/'openclaw.data').read_bytes(), compresslevel=9, mtime=0)
wasm_gz=gzip.compress((root/'openclaw.wasm').read_bytes(), compresslevel=9, mtime=0)
data_b64=base64.b64encode(data_gz).decode('ascii')
wasm_b64=base64.b64encode(wasm_gz).decode('ascii')

head=r'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="theme-color" content="#000000"><title>OpenClaw v1.03 — Full Real Mobile V3</title>
<style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#000;color:#fff;font-family:Arial,Helvetica,sans-serif;touch-action:none;overscroll-behavior:none;-webkit-user-select:none;user-select:none}
#gameShell{position:fixed;inset:0;background:#000;display:flex;align-items:center;justify-content:center}#canvas{display:block;width:100vw;height:100dvh;object-fit:contain;background:#000;outline:0;touch-action:none}
#boot{position:fixed;inset:0;z-index:1000;background:radial-gradient(circle at 50% 35%,#382309 0,#130c05 34%,#020202 74%);display:flex;align-items:center;justify-content:center;padding:22px;box-sizing:border-box}#boot.hidden{display:none}
#panel{width:min(760px,94vw);max-height:92dvh;overflow:auto;text-align:center;background:rgba(0,0,0,.84);border:1px solid rgba(255,190,65,.45);border-radius:20px;padding:24px;box-sizing:border-box;box-shadow:0 14px 70px #000}
#title{font-size:clamp(28px,6vw,54px);font-weight:900;letter-spacing:.04em;color:#f5b53a;text-shadow:0 2px 0 #5d3200;margin-bottom:4px}#subtitle{font-size:13px;opacity:.75;margin-bottom:18px}
#status{font-size:16px;min-height:24px;margin:12px 0}#bar{height:12px;border-radius:8px;background:#24180b;overflow:hidden;border:1px solid #6f4b19}#fill{height:100%;width:0;background:linear-gradient(90deg,#b76a14,#ffd066);transition:width .15s linear}
#detail{margin-top:9px;font-size:12px;opacity:.7;min-height:18px;word-break:break-word}#start{font-size:21px;font-weight:800;padding:13px 28px;border:2px solid #ffd36b;border-radius:14px;background:linear-gradient(#d78b22,#864810);color:#fff;text-shadow:0 1px 2px #000;box-shadow:0 6px 24px #000;cursor:pointer}
#topTools{position:fixed;z-index:1100;right:max(10px,env(safe-area-inset-right));top:max(10px,env(safe-area-inset-top));display:flex;gap:8px}.tool{border:1px solid rgba(255,255,255,.35);background:rgba(0,0,0,.62);color:#fff;border-radius:11px;padding:9px 12px;font-weight:700;font-size:13px}
#diag{display:none;margin-top:12px;text-align:left;background:#080808;border:1px solid #555;border-radius:10px;padding:10px;max-height:34vh;overflow:auto;white-space:pre-wrap;font:11px/1.35 monospace;color:#d7f3d7}#diag.bad{display:block;border-color:#a33;color:#ffd7d7;background:#210606}
#diagFloat{display:none;position:fixed;z-index:1050;left:max(8px,env(safe-area-inset-left));bottom:max(8px,env(safe-area-inset-bottom));width:min(92vw,760px);max-height:34vh;overflow:auto;background:rgba(0,0,0,.9);border:1px solid #555;border-radius:10px;padding:9px;box-sizing:border-box;white-space:pre-wrap;font:10px/1.3 monospace;color:#d8ffd8;pointer-events:auto}
@media(orientation:portrait){#detail:after{content:' • Rotate to landscape';color:#ffd36b}}
</style></head><body>
<div id="gameShell"><canvas id="canvas" width="960" height="540" tabindex="-1" oncontextmenu="event.preventDefault()"></canvas></div>
<div id="topTools"><button class="tool" id="logBtn">LOG</button><button class="tool" id="fsBtn">⛶ Fullscreen</button></div>
<div id="diagFloat"></div>
<div id="boot"><div id="panel"><div id="title">OPENCLAW</div><div id="subtitle">Real pjasicek/OpenClaw C++ engine • Official v1.03 resources • Android-safe V3</div><button id="start">START CAPTAIN CLAW</button><div id="status">Tap Start to unpack the embedded real game.</div><div id="bar"><div id="fill"></div></div><div id="detail">This build waits for the C++ engine itself to confirm successful initialization.</div><div id="diag"></div></div></div>
<script>
(function(){'use strict';
const boot=document.getElementById('boot'),statusEl=document.getElementById('status'),fill=document.getElementById('fill'),detail=document.getElementById('detail'),diag=document.getElementById('diag'),diagFloat=document.getElementById('diagFloat'),start=document.getElementById('start'),canvas=document.getElementById('canvas');
let failed=false,gameReady=false,runtimeReady=false,logs=[];
function setStatus(t,p,d){statusEl.textContent=t;if(Number.isFinite(p))fill.style.width=Math.max(0,Math.min(100,p))+'%';if(d!==undefined)detail.textContent=d}
function addLog(level,args){let line='['+level+'] '+Array.from(args).map(x=>{try{return typeof x==='string'?x:JSON.stringify(x)}catch(_){return String(x)}}).join(' ');logs.push(line);if(logs.length>180)logs.splice(0,logs.length-180);let text=logs.slice(-80).join('\n');diag.textContent=text;diagFloat.textContent=text;if(/OPENCLAW_BROWSER_GAME_READY/.test(line)){gameReady=true;setStatus('Captain Claw initialized successfully',100,'The real game engine is running.');setTimeout(()=>{boot.classList.add('hidden');canvas.focus()},550)}if(/Failed to initialize\. Exiting|Could not load game options|Failed to create SDL2 Renderer|Failed to initialize resource|Failed to load TTF|abort\(/i.test(line)&&!gameReady){showFailure('The OpenClaw engine reported a startup failure.')}}
for(const k of ['log','warn','error']){const old=console[k].bind(console);console[k]=function(){old(...arguments);addLog(k.toUpperCase(),arguments)}}
function showFailure(msg){failed=true;boot.classList.remove('hidden');diag.classList.add('bad');diag.style.display='block';setStatus(msg,100,'Send a screenshot of the log below if the game does not continue.');fill.style.background='#b32323';start.style.display='inline-block';start.disabled=false;start.textContent='RELOAD';start.onclick=()=>location.reload()}
window.addEventListener('error',e=>{addLog('WINDOW-ERROR',[e.message]);if(!gameReady)showFailure('JavaScript/WebAssembly startup error')});window.addEventListener('unhandledrejection',e=>{addLog('PROMISE',[e.reason]);if(!gameReady)showFailure('OpenClaw startup promise failed')});
function toggleLogs(){let on=diagFloat.style.display==='block';diagFloat.style.display=on?'none':'block'}document.getElementById('logBtn').onclick=toggleLogs;
async function fullscreen(){try{if(!document.fullscreenElement&&document.documentElement.requestFullscreen)await document.documentElement.requestFullscreen({navigationUI:'hide'})}catch(_){}try{if(screen.orientation&&screen.orientation.lock)await screen.orientation.lock('landscape')}catch(_){}}
document.getElementById('fsBtn').onclick=fullscreen;
function resumeAudio(){try{if(window.SDL2&&SDL2.audioContext&&SDL2.audioContext.state==='suspended')SDL2.audioContext.resume()}catch(_){}}document.addEventListener('pointerdown',resumeAudio,{passive:true});
function decodeGzip(el,label,p0,p1){return new Promise(async(resolve,reject)=>{try{if(typeof DecompressionStream==='undefined')throw new Error('Chrome DecompressionStream is unavailable. Update Chrome.');let text=el.textContent,pos=0,total=text.length,CH=1024*1024;const stream=new ReadableStream({pull(c){if(pos>=total){c.close();el.remove();return}let end=Math.min(total,pos+CH);end-=((end-pos)%4);if(end<=pos)end=total;let bin=atob(text.slice(pos,end));pos=end;let b=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)b[i]=bin.charCodeAt(i);c.enqueue(b);let q=pos/total;setStatus('Unpacking '+label+'…',p0+(p1-p0)*q,Math.round(q*100)+'% decoded')}});let buf=await new Response(stream.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();text=null;resolve(buf)}catch(e){reject(e)}})}
async function launch(){failed=false;gameReady=false;start.disabled=true;start.style.display='none';diag.style.display='none';fullscreen();try{setStatus('Preparing original Captain Claw resources…',2,'Unpacking the embedded CLAW.REZ data package.');const dataBuf=await decodeGzip(document.getElementById('ocData'),'game data',3,57);setStatus('Preparing OpenClaw WebAssembly…',59,(dataBuf.byteLength/1048576).toFixed(1)+' MB game package ready');const wasmBuf=await decodeGzip(document.getElementById('ocWasm'),'engine',59,77);let preload=dataBuf;window.Module={canvas,preRun:[],wasmBinary:new Uint8Array(wasmBuf),getPreloadedPackage:function(name,size){if(String(name).includes('openclaw.data')&&preload){let b=preload;preload=null;setStatus('Creating game filesystem…',82,'Mounting real CLAW.REZ and ASSETS.ZIP');return b}return null},setStatus:function(t){if(t)setStatus(t,86,'OpenClaw runtime')},print:function(){addLog('OUT',arguments)},printErr:function(){addLog('ERR',arguments)},onRuntimeInitialized:function(){runtimeReady=true;setStatus('Runtime ready — initializing OpenClaw C++…',91,'Waiting for display, audio, resources, fonts and game logic.');resumeAudio();setTimeout(()=>{if(!gameReady)showFailure('The WebAssembly runtime started, but OpenClaw did not finish C++ initialization.')},18000)},onAbort:function(r){addLog('ABORT',[r]);showFailure('OpenClaw aborted during startup')}};const src=document.getElementById('ocEngine').textContent;document.getElementById('ocEngine').remove();let s=document.createElement('script');s.text=src+'\n//# sourceURL=openclaw-inline.js';document.body.appendChild(s)}catch(e){addLog('BOOT',[e&&e.stack||e]);showFailure('The standalone OpenClaw loader failed.')}}
start.addEventListener('click',launch,{once:true});setStatus('Ready',0,'Tap START CAPTAIN CLAW.');
})();
</script>'''

mid='\n<script type="application/octet-stream" id="ocData">'+data_b64+'</script>\n<script type="application/octet-stream" id="ocWasm">'+wasm_b64+'</script>\n'
tail='\n<script type="text/plain" id="ocEngine">'+engine+'</script>\n</body></html>\n'
out.write_text(head+mid+tail,encoding='utf-8')
print(f'Created {out} ({out.stat().st_size} bytes)')
