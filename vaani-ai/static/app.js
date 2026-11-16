const $ = (id) => document.getElementById(id);
const log = $("log"), textIn = $("text");
let LANGS = [], recognizing = false, recog = null;

try { const t = localStorage.getItem("theme"); if (t) document.documentElement.dataset.theme = t; } catch (e) {}
$("themeBtn").onclick = () => {
  const cur = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = cur;
  try { localStorage.setItem("theme", cur); } catch (e) {}
};

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function addMsg(who, text, sub) {
  const d = document.createElement("div");
  d.className = "msg " + who;
  d.innerHTML = `<div class="bubble">${esc(text)}${sub ? `<small>${esc(sub)}</small>` : ""}</div>`;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

async function init() {
  LANGS = await (await fetch("/api/languages")).json();
  for (const l of LANGS) {
    $("speechLang").insertAdjacentHTML("beforeend", `<option value="${l.speech}" data-code="${l.code}">${l.name}</option>`);
    $("replyLang").insertAdjacentHTML("beforeend", `<option value="${l.code}">${l.name}</option>`);
    $("transLang").insertAdjacentHTML("beforeend", `<option value="${l.code}">${l.name}</option>`);
  }
  $("transLang").value = "en";
  const samples = ["What time is it?", "मेरा नाम राहुल है", "Tell me a joke", "translate good morning to Hindi",
    "Estoy muy triste", "aaj ki tareekh kya hai", "Bonjour, merci beaucoup", "I am so happy today!"];
  $("chips").innerHTML = samples.map((s) => `<button type="button" class="chip">${esc(s)}</button>`).join("");
  $("chips").onclick = (e) => { if (e.target.classList.contains("chip")) send(e.target.textContent); };
}

// ---------- Voice input (Web Speech API) ----------
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SR) { $("micBtn").title = "Voice input needs Chrome or Edge – you can still type or upload audio."; $("micBtn").style.opacity = .5; }
$("micBtn").onclick = () => {
  if (!SR) { alert("Your browser doesn't support live speech recognition. Use Chrome/Edge, or type / upload a WAV file."); return; }
  if (recognizing) { recog.stop(); return; }
  recog = new SR();
  const sel = $("speechLang").value;
  recog.lang = sel === "auto" ? "en-IN" : sel;
  recog.interimResults = true;
  recog.onstart = () => { recognizing = true; $("micBtn").classList.add("on"); };
  recog.onend = () => { recognizing = false; $("micBtn").classList.remove("on"); $("interim").hidden = true; };
  recog.onerror = (e) => { addMsg("bot", "Microphone error: " + e.error + ". You can type instead."); };
  recog.onresult = (ev) => {
    let interim = "", final = "";
    for (const r of ev.results) (r.isFinal ? (final += r[0].transcript) : (interim += r[0].transcript));
    $("interim").hidden = false; $("interim").textContent = "🎙 " + (final || interim);
    if (final) { send(final.trim()); recog.stop(); }
  };
  recog.start();
};

// ---------- Audio-file upload ----------
$("file").onchange = async (e) => {
  const f = e.target.files[0]; if (!f) return;
  const fd = new FormData(); fd.append("audio", f);
  const sel = $("speechLang").selectedOptions[0];
  fd.append("lang", sel && sel.dataset.code ? sel.dataset.code : "en");
  addMsg("bot", "Transcribing " + f.name + "…");
  const r = await fetch("/api/transcribe", { method: "POST", body: fd });
  const j = await r.json();
  if (j.ok) send(j.text); else addMsg("bot", j.error);
  e.target.value = "";
};

// ---------- Send / render ----------
$("form").onsubmit = (e) => { e.preventDefault(); const t = textIn.value.trim(); if (t) send(t); };

async function send(text) {
  textIn.value = "";
  addMsg("user", text);
  let res;
  try {
    const r = await fetch("/api/analyze", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, reply_to: $("replyLang").value, translate_to: $("transLang").value,
        tz: Intl.DateTimeFormat().resolvedOptions().timeZone }),
    });
    res = await r.json();
    if (!r.ok) throw new Error(res.error || "Request failed");
  } catch (err) { addMsg("bot", "Error: " + err.message); return; }
  const rep = res.reply;
  addMsg("bot", rep.text, rep.lang !== "en" ? "EN: " + rep.english : "");
  render(res);
  if ($("ttsOn").checked && "speechSynthesis" in window) {
    const u = new SpeechSynthesisUtterance(rep.text); u.lang = rep.tts; speechSynthesis.cancel(); speechSynthesis.speak(u);
  }
}

function render(r) {
  $("empty").hidden = true; $("cards").hidden = false;
  const L = r.language;
  $("langOut").innerHTML = `<div class="row"><span>Detected</span><b>${esc(L.name)}</b></div>
    <div class="row"><span>Confidence</span><span>${(L.confidence * 100).toFixed(0)}% · ${esc(L.method)}</span></div>
    <div class="bar"><i style="width:${L.confidence * 100}%"></i></div>`;
  const P = r.preprocessing;
  $("prepOut").innerHTML = `<div class="row"><span>Normalised</span></div><div>${esc(P.normalized)}</div>
    <div class="row"><span>Tokens</span></div><div>${P.tokens.map((t) => `<span class="tag">${esc(t)}</span>`).join("")}</div>
    <div class="row"><span>Stop-words removed</span></div><div>${P.without_stopwords.map((t) => `<span class="tag">${esc(t)}</span>`).join("") || "—"}</div>
    <div class="row"><span>Stems</span></div><div>${P.stems.map((t) => `<span class="tag">${esc(t)}</span>`).join("") || "—"}</div>`;
  const S = r.sentiment, cls = { positive: "pos", negative: "neg", neutral: "neu" }[S.label];
  $("sentOut").innerHTML = `<span class="tag ${cls}">${esc(S.label)}</span> <span class="muted">score ${S.compound}</span>
    <div class="meter"><b style="left:${((S.compound + 1) / 2) * 100}%"></b></div>
    <div class="muted" style="font-size:12px">${esc(S.method)}</div>`;
  const I = r.intent;
  $("intentOut").innerHTML = `<div class="row"><span>Intent</span><b>${esc(I.name)}</b></div>
    ${I.ranked.map(([n, p]) => `<div class="row"><span>${esc(n)}</span><span>${(p * 100).toFixed(0)}%</span></div><div class="bar"><i style="width:${p * 100}%"></i></div>`).join("")}
    <div class="row"><span>Entities</span></div><div>${r.entities.length ? r.entities.map((e) => `<span class="tag">${esc(e.type)}: ${esc(e.value)}</span>`).join("") : '<span class="muted">none found</span>'}</div>`;
  const T = r.translation;
  $("transOut").innerHTML = `<div class="row"><span>→ ${esc(T.target_name)}</span><span class="muted">${esc(T.engine)}</span></div>
    <div>${T.ok ? esc(T.text) : '<span class="muted">Translation unavailable offline for this sentence (needs internet).</span>'}</div>`;
}
init();
