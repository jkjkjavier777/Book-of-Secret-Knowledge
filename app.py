import threading
import urllib.request

from flask import Flask, jsonify, request

from core.generator import Generator
from core.memory import Memory
from learning import corpus

app = Flask(__name__)
gen = Generator()
mem = Memory()
lock = threading.Lock()

PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Book of Secret Knowledge</title>
<style>
:root{--bg:#fffaf0;--panel:#fff;--ink:#1f1a14;--mute:#7a6f63;--line:#eadfce;--acc:#fa520f;--acc2:#ffaf00;--me:#ffeedb}
@media (prefers-color-scheme:dark){:root{--bg:#15110d;--panel:#1e1913;--ink:#f6efe4;--mute:#a09384;--line:#322a20;--me:#2b2217}}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif;display:flex;flex-direction:column;height:100dvh;padding-top:env(safe-area-inset-top)}
header{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-bottom:1px solid var(--line)}
.tabs{display:flex;gap:4px;background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:3px}
.tabs button{border:0;background:none;color:var(--mute);padding:6px 16px;border-radius:999px;font:inherit;font-size:14px}
.tabs button.on{background:linear-gradient(135deg,var(--acc2),var(--acc));color:#fff}
.stat{font-size:13px;color:var(--mute);display:flex;align-items:center;gap:6px}
.dot{width:8px;height:8px;border-radius:50%;background:#999}
.dot.up{background:#2fb344}
main{flex:1;overflow-y:auto;padding:16px 14px}
.msg{max-width:88%;margin:0 0 12px;padding:10px 14px;border-radius:18px;white-space:pre-wrap;overflow-wrap:anywhere}
.me{margin-left:auto;background:var(--me)}
.bot{background:var(--panel);border:1px solid var(--line)}
.wait{color:var(--mute)}
.sys{color:var(--mute);font-size:13px;text-align:center;margin:0 0 12px}
.acts{display:flex;gap:6px;margin:-4px 0 12px}
.acts button,.chip{border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;padding:5px 14px;font:inherit;font-size:14px}
#hero{text-align:center;margin-top:12vh}
#hero h1{font-size:28px;margin:0 0 6px;background:linear-gradient(135deg,var(--acc2),var(--acc));-webkit-background-clip:text;background-clip:text;color:transparent}
#hero p{color:var(--mute);margin:0 0 18px}
#hero .chip{margin:4px}
footer{display:flex;gap:8px;padding:10px 14px calc(10px + env(safe-area-inset-bottom));border-top:1px solid var(--line)}
#box{flex:1;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;padding:11px 16px;font:inherit;outline:none}
#go{border:0;border-radius:50%;width:44px;height:44px;color:#fff;font-size:20px;background:linear-gradient(135deg,var(--acc2),var(--acc))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:0 0 10px}
.card small{color:var(--mute)}
h3{margin:18px 0 8px;font-size:15px;color:var(--mute);font-weight:600}
</style></head><body>
<header>
  <div class="tabs"><button id="t-chat" class="on">Chat</button><button id="t-learn">Learned</button></div>
  <div class="stat"><span class="dot" id="dot"></span><span id="st">checking</span></div>
</header>
<main id="feed">
  <div id="hero">
    <h1>Book of Secret Knowledge</h1>
    <p>What are we digging into?</p>
    <button class="chip">hello</button><button class="chip">tell me a secret</button><button class="chip">what are you really?</button>
  </div>
</main>
<main id="learned" style="display:none"></main>
<footer><input id="box" placeholder="Message" autocomplete="off"><button id="go">&#8593;</button></footer>
<script>
const $=s=>document.querySelector(s);
const feed=$('#feed'),learned=$('#learned'),box=$('#box');
let mode='chat',busy=false,acts=null;

function add(cls,text){const d=document.createElement('div');d.className=cls==='sys'?'sys':'msg '+cls;d.textContent=text;feed.appendChild(d);feed.scrollTop=feed.scrollHeight;return d}
async function post(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return r.json()}
function note(n){if(n)add('sys',n)}
function clearActs(){if(acts){acts.remove();acts=null}}
function showActs(){
  clearActs();
  acts=document.createElement('div');acts.className='acts';
  [['+','Keep'],['-','Drop'],['correct','Correct']].forEach(function(p){
    const b=document.createElement('button');b.textContent=p[1];
    b.onclick=function(){p[0]==='correct'?startCorrect():rate(p[0])};
    acts.appendChild(b);
  });
  feed.appendChild(acts);feed.scrollTop=feed.scrollHeight;
}
async function rate(a){clearActs();const j=await post('/feedback',{action:a});note(j.note)}
function startCorrect(){clearActs();mode='correct';box.placeholder='Type the better answer';box.focus()}
async function send(t){
  t=(t||box.value).trim();
  if(!t||busy)return;
  box.value='';
  if(mode==='correct'){
    mode='chat';box.placeholder='Message';
    const j=await post('/feedback',{action:'correct',text:t});note(j.note);return;
  }
  $('#hero').style.display='none';clearActs();add('me',t);busy=true;
  const w=add('bot wait','thinking...');
  try{const j=await post('/chat',{text:t});w.className='msg bot';w.textContent=j.reply||'(no reply)';showActs()}
  catch(e){w.textContent='(connection lost)'}
  busy=false;
}
$('#go').onclick=function(){send()};
box.addEventListener('keydown',function(e){if(e.key==='Enter')send()});
document.querySelectorAll('.chip').forEach(function(c){c.onclick=function(){send(c.textContent)}});

function card(a,b){const d=document.createElement('div');d.className='card';d.textContent=a;if(b){const s=document.createElement('small');s.textContent=' '+b;d.appendChild(document.createElement('br'));d.appendChild(s)}return d}
async function loadLearned(){
  const j=await (await fetch('/learned')).json();
  learned.textContent='';
  const h1=document.createElement('h3');h1.textContent='Corrections you taught';learned.appendChild(h1);
  const keys=Object.keys(j.corrections);
  if(!keys.length)learned.appendChild(card('Nothing yet.','Use Correct under a reply.'));
  keys.forEach(function(k){learned.appendChild(card(k,j.corrections[k].join(' | ')))});
  const h2=document.createElement('h3');h2.textContent='Replies by score';learned.appendChild(h2);
  if(!j.scores.length)learned.appendChild(card('No ratings yet.'));
  j.scores.forEach(function(s){learned.appendChild(card(s[0],'score '+s[1]))});
}
function tab(which){
  $('#t-chat').className=which==='chat'?'on':'';
  $('#t-learn').className=which==='learn'?'on':'';
  feed.style.display=which==='chat'?'':'none';
  learned.style.display=which==='learn'?'':'none';
  if(which==='learn')loadLearned();
}
$('#t-chat').onclick=function(){tab('chat')};
$('#t-learn').onclick=function(){tab('learn')};

async function status(){
  try{const j=await (await fetch('/status')).json();
    $('#dot').className='dot'+(j.llm?' up':'');
    $('#st').textContent=j.llm?'LLM online':'LLM offline: rules only';
  }catch(e){$('#st').textContent='server down'}
}
status();setInterval(status,15000);
</script></body></html>'''


@app.get("/")
def index():
    return PAGE


@app.post("/chat")
def chat():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not text:
        return jsonify(error="empty"), 400
    with lock:
        mem.add("you", text)
        reply = gen.reply(text, mem.history())
        mem.add("bot", reply)
    return jsonify(reply=reply)


@app.post("/feedback")
def feedback():
    d = request.get_json(silent=True) or {}
    act = d.get("action")
    if act in ("+", "-"):
        cmd = act
    elif act == "correct" and d.get("text", "").strip():
        cmd = "say it like this: " + " ".join(d["text"].split())
    else:
        return jsonify(error="bad request"), 400
    with lock:
        note = gen.learner.handle(cmd)
        if gen.learner.to_log:
            corpus.append(*gen.learner.to_log)
    return jsonify(note=note)


@app.get("/learned")
def learned():
    d = gen.learner.data
    scores = sorted(d["scores"].items(), key=lambda kv: -kv[1])
    return jsonify(corrections=d["corrections"], scores=scores[:8])


@app.get("/status")
def status():
    try:
        urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=1).read()
        return jsonify(llm=True)
    except Exception:
        return jsonify(llm=False)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
