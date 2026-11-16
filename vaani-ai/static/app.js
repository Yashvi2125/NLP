const $ = (id) => document.getElementById(id);
const log = $("log"), textIn = $("text");
let LANGS = [], recognizing = false, recog = null;
let currentSource = "text";
let lastAudioMeta = null;

// Multi-turn session persistence
let sessionId = localStorage.getItem("vaani_session_id");
if (!sessionId) {
  sessionId = "sess-" + Math.random().toString(36).substring(2, 12);
  localStorage.setItem("vaani_session_id", sessionId);
}

// Theme toggler
try {
  const t = localStorage.getItem("theme");
  if (t) document.documentElement.dataset.theme = t;
} catch (e) {}

$("themeBtn").onclick = () => {
  const cur = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = cur;
  try { localStorage.setItem("theme", cur); } catch (e) {}
};

const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"
}[c]));

function formatEngineBadge(engine, model) {
  const eng = String(engine || "").toLowerCase();
  if (eng.includes("gemini")) {
    const modelTag = model ? ` · ${model.replace("gemini-", "")}` : "";
    return { cls: "gemini", text: "Gemini AI" + modelTag };
  }
  if (eng.includes("fallback") || eng.includes("offline")) {
    return { cls: "offline", text: "Offline Fallback" };
  }
  return { cls: "local", text: "Local Engine" };
}

function formatTime(d = new Date()) {
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function showInterim(text, type = "info") {
  const el = $("interim");
  if (!el) return;
  el.className = "interim " + (type === "error" ? "error" : type === "success" ? "success" : "");
  el.textContent = text;
  el.hidden = false;
}

function hideInterim(delayMs = 0) {
  const el = $("interim");
  if (!el) return;
  if (delayMs > 0) {
    setTimeout(() => { el.hidden = true; }, delayMs);
  } else {
    el.hidden = true;
  }
}

// ---------- Chat message rendering ----------
function addMsg(who, text, sub, badgeHtml, source = null, latencyMs = null) {
  const d = document.createElement("div");
  d.className = "msg " + who;

  const timeStr = formatTime();
  let sourceBadge = "";
  if (source === "voice") {
    sourceBadge = `<span class="msg-source">🎙️ Voice</span>`;
  } else if (source === "audio") {
    sourceBadge = `<span class="msg-source">📎 Audio file</span>`;
  }

  let latencyBadge = "";
  if (latencyMs != null && latencyMs > 0) {
    latencyBadge = `<span>⚡ ${latencyMs >= 1000 ? (latencyMs / 1000).toFixed(2) + "s" : latencyMs.toFixed(0) + "ms"}</span>`;
  }

  const metaHtml = `
    <div class="msg-meta">
      <div>${sourceBadge}</div>
      <div style="display:flex;gap:6px;align-items:center;">
        ${latencyBadge}
        <span>${timeStr}</span>
      </div>
    </div>
  `;

  d.innerHTML = `
    <div class="bubble">
      ${badgeHtml || ""}
      <div>${esc(text)}</div>
      ${sub ? `<small>${esc(sub)}</small>` : ""}
      ${metaHtml}
    </div>
  `;

  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

// Typing indicator bubble
function showTyping() {
  hideTyping();
  const d = document.createElement("div");
  d.className = "msg bot typing";
  d.id = "typingBubble";
  d.innerHTML = `
    <div class="bubble" style="padding:10px 14px;">
      <div class="typing-dots"><span></span><span></span><span></span></div>
      <small style="margin-top:2px;">Analyzing language &amp; generating response…</small>
    </div>
  `;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

function hideTyping() {
  const el = $("typingBubble");
  if (el) el.remove();
}

// Mobile responsive tab switcher
if ($("tabChatBtn") && $("tabInsightsBtn")) {
  $("tabChatBtn").onclick = () => {
    $("tabChatBtn").classList.add("active");
    $("tabInsightsBtn").classList.remove("active");
    $("chatPanel").classList.remove("mobile-hidden");
    $("insights").classList.add("mobile-hidden");
  };
  $("tabInsightsBtn").onclick = () => {
    $("tabInsightsBtn").classList.add("active");
    $("tabChatBtn").classList.remove("active");
    $("chatPanel").classList.add("mobile-hidden");
    $("insights").classList.remove("mobile-hidden");
  };
}

// Reset conversational memory button
if ($("resetChatBtn")) {
  $("resetChatBtn").onclick = async () => {
    try {
      await fetch("/api/chat/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
    } catch (e) {}

    sessionId = "sess-" + Math.random().toString(36).substring(2, 12);
    localStorage.setItem("vaani_session_id", sessionId);

    log.innerHTML = `
      <div class="msg bot">
        <div class="bubble">
          <span class="badge local">Local Engine</span>
          <div>Memory reset! A fresh conversation session has started. How can I help you today?</div>
          <div class="msg-meta"><span>${formatTime()}</span></div>
        </div>
      </div>
    `;
    $("empty").hidden = false;
    $("cards").hidden = true;
    if ($("insightsBadge")) $("insightsBadge").style.display = "none";
  };
}

// Initialize language dropdowns and sample suggestion chips
async function init() {
  try {
    LANGS = await (await fetch("/api/languages")).json();
    for (const l of LANGS) {
      $("speechLang").insertAdjacentHTML("beforeend", `<option value="${l.speech}" data-code="${l.code}">${l.name}</option>`);
      $("replyLang").insertAdjacentHTML("beforeend", `<option value="${l.code}">${l.name}</option>`);
      $("transLang").insertAdjacentHTML("beforeend", `<option value="${l.code}">${l.name}</option>`);
    }
    $("transLang").value = "en";
  } catch (err) {
    console.error("Failed to load languages:", err);
  }

  const samples = [
    "What time is it?",
    "मेरा नाम राहुल है",
    "Tell me a joke",
    "Who is the CEO of Google?",
    "Estoy muy triste",
    "aaj ki tareekh kya hai",
    "Bonjour, merci beaucoup",
    "I am so happy today!",
  ];
  $("chips").innerHTML = samples.map((s) => `<button type="button" class="chip">${esc(s)}</button>`).join("");
  $("chips").onclick = (e) => {
    if (e.target.classList.contains("chip")) {
      currentSource = "text";
      lastAudioMeta = null;
      send(e.target.textContent, "text");
    }
  };
}

// ---------- Voice input (Web Speech API) ----------
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SR) {
  $("micBtn").title = "Live voice input requires Chrome or Edge. You can still upload audio files or type.";
  $("micBtn").style.opacity = .5;
}

$("micBtn").onclick = () => {
  if (!SR) {
    alert("Your browser does not support the Web Speech API for live speech recognition. Please use Google Chrome or Microsoft Edge, or upload an audio file via the paperclip button.");
    return;
  }
  if (recognizing) {
    recog.stop();
    return;
  }

  try {
    recog = new SR();
  } catch (err) {
    showInterim("⚠️ Could not initialize speech recognition: " + err.message, "error");
    return;
  }

  const sel = $("speechLang").value;
  recog.lang = sel === "auto" ? "en-IN" : sel;
  recog.interimResults = true;
  recog.maxAlternatives = 1;

  recog.onstart = () => {
    recognizing = true;
    $("micBtn").classList.add("on");
    $("micBtn").title = "Listening… Click to stop";
    showInterim("🎙️ Listening… Speak clearly in your selected language.", "info");
  };

  recog.onend = () => {
    recognizing = false;
    $("micBtn").classList.remove("on");
    $("micBtn").title = "Start voice input (Click to speak)";
    hideInterim(3000);
  };

  recog.onerror = (e) => {
    recognizing = false;
    $("micBtn").classList.remove("on");
    const errMap = {
      "not-allowed": "Microphone permission denied. Please allow microphone access in your browser settings.",
      "service-not-allowed": "Microphone permission denied by operating system.",
      "no-speech": "No speech detected. Please speak closer to your microphone and try again.",
      "audio-capture": "No microphone detected or microphone is in use by another application.",
      "network": "Speech recognition network timeout or connectivity error.",
      "language-not-supported": "Selected language is not supported by your browser's speech recognition engine.",
      "aborted": "Speech input was cancelled.",
    };
    const notice = errMap[e.error] || ("Microphone error: " + e.error);
    showInterim("⚠️ " + notice, "error");
    addMsg("bot", "Notice: " + notice + " You can type or upload an audio file instead.");
  };

  recog.onresult = (ev) => {
    let interim = "";
    let finalTranscript = "";

    for (let i = ev.resultIndex; i < ev.results.length; ++i) {
      const res = ev.results[i];
      if (res.isFinal) {
        finalTranscript += res[0].transcript;
      } else {
        interim += res[0].transcript;
      }
    }

    if (interim) {
      showInterim("🎙️ " + interim, "info");
    }

    if (finalTranscript) {
      const clean = finalTranscript.trim();
      textIn.value = clean;
      textIn.focus();
      showInterim("✅ Recognized: \"" + clean + "\" (Review or press Send)", "success");

      const autoSend = $("autoSendVoice") && $("autoSendVoice").checked;
      if (autoSend) {
        currentSource = "voice";
        lastAudioMeta = { engine: "Browser Web Speech API", source: "voice" };
        send(clean, "voice", lastAudioMeta);
      }
      recog.stop();
    }
  };

  try {
    recog.start();
  } catch (err) {
    showInterim("⚠️ Failed to start microphone: " + err.message, "error");
  }
};

// ---------- Audio-file upload ----------
$("file").onchange = async (e) => {
  const f = e.target.files[0];
  if (!f) return;

  if (f.size > 10 * 1024 * 1024) {
    alert("Audio file is too large (" + (f.size / (1024 * 1024)).toFixed(1) + " MB). Maximum allowed size is 10 MB.");
    e.target.value = "";
    return;
  }

  const fd = new FormData();
  fd.append("audio", f);
  const sel = $("speechLang").selectedOptions[0];
  const langCode = sel && sel.dataset.code ? sel.dataset.code : "en";
  fd.append("lang", langCode);
  fd.append("session_id", sessionId);

  showInterim("⏳ Transcribing audio file (" + f.name + ")…", "info");
  addMsg("bot", "Uploading and transcribing " + f.name + " (" + (f.size / 1024).toFixed(1) + " KB)…");

  try {
    const r = await fetch("/api/transcribe", { method: "POST", body: fd });
    const j = await r.json();
    if (j.ok && j.text) {
      textIn.value = j.text;
      textIn.focus();
      showInterim("✅ Transcribed: \"" + j.text + "\" (" + j.engine + ", " + (j.latency_ms || 0).toFixed(0) + " ms)", "success");
      hideInterim(4000);

      lastAudioMeta = {
        engine: j.engine,
        source: "audio",
        filename: f.name,
        latency_ms: j.latency_ms,
        duration_sec: j.duration_sec,
      };

      const autoSend = $("autoSendVoice") && $("autoSendVoice").checked;
      if (autoSend) {
        currentSource = "audio";
        send(j.text, "audio", lastAudioMeta);
      }
    } else {
      const err = j.error || "Audio transcription failed.";
      showInterim("⚠️ " + err, "error");
      addMsg("bot", "Transcription error: " + err);
    }
  } catch (err) {
    showInterim("⚠️ Network error while uploading audio: " + err.message, "error");
    addMsg("bot", "Network error during transcription: " + err.message);
  }
  e.target.value = "";
};

// ---------- Send / render ----------
$("form").onsubmit = (e) => {
  e.preventDefault();
  const t = textIn.value.trim();
  if (t) {
    const src = currentSource || "text";
    const meta = lastAudioMeta;
    // Reset after sending
    currentSource = "text";
    lastAudioMeta = null;
    send(t, src, meta);
  }
};

async function send(text, source = "text", audioMeta = null) {
  textIn.value = "";
  addMsg("user", text, null, null, source);
  showTyping();

  const clientStartTime = performance.now();
  let res;

  try {
    const r = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        session_id: sessionId,
        reply_to: $("replyLang").value,
        translate_to: $("transLang").value,
        tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
      }),
    });
    res = await r.json();
    if (!r.ok) throw new Error(res.error || "Request failed");
  } catch (err) {
    hideTyping();
    addMsg("bot", "Error: " + err.message);
    return;
  }

  hideTyping();
  const rep = res.reply;
  const clientTotalMs = performance.now() - clientStartTime;

  let badgeHtml = "";
  if (rep.engine) {
    const b = formatEngineBadge(rep.engine, rep.model);
    badgeHtml = `<div><span class="badge ${b.cls}">${esc(b.text)}</span></div>`;
  }

  addMsg(
    "bot",
    rep.text,
    rep.lang !== "en" && rep.english !== rep.text ? "EN: " + rep.english : "",
    badgeHtml,
    null,
    rep.latency_ms || clientTotalMs
  );

  render(res, audioMeta, clientTotalMs);

  if ($("ttsOn").checked && "speechSynthesis" in window) {
    const u = new SpeechSynthesisUtterance(rep.text);
    u.lang = rep.tts;
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
  }
}

// ---------- NLP Transparency Cards Render ----------
function render(r, audioMeta = null, clientTotalMs = null) {
  $("empty").hidden = true;
  $("cards").hidden = false;

  // 1. Language Identification
  const L = r.language;
  $("langOut").innerHTML = `
    <div class="row"><span>Detected Language</span><b>${esc(L.name)} (${esc(L.native || L.name)})</b></div>
    <div class="row"><span>Confidence</span><span>${(L.confidence * 100).toFixed(0)}%</span></div>
    <div class="bar"><i style="width:${Math.min(100, L.confidence * 100)}%"></i></div>
    <div class="row"><span>Detection Method</span><span>${esc(L.method || "Script Analysis")}</span></div>
    <div class="row"><span>Script Family</span><span class="tag">${esc(L.script || "General")}</span></div>
  `;

  // 2. Preprocessing & Normalization
  const P = r.preprocessing;
  $("prepOut").innerHTML = `
    <div class="row"><span>Normalized Output</span></div>
    <div style="font-size:13px;background:var(--soft);padding:6px 10px;border-radius:8px;margin-bottom:6px;">${esc(P.normalized)}</div>
    ${P.hinglish_normalized && P.hinglish_normalized !== P.normalized ? `
      <div class="row"><span>Hinglish Phonetic</span></div>
      <div style="font-size:13px;background:var(--soft);padding:6px 10px;border-radius:8px;margin-bottom:6px;">${esc(P.hinglish_normalized)}</div>
    ` : ""}
    ${P.is_mixed ? `
      <div class="row"><span>Mixed Scripts</span><b>${esc(P.active_scripts ? P.active_scripts.join(" + ") : "Mixed")}</b></div>
    ` : ""}
    <div class="row" style="margin-top:6px;"><span>Tokens (${P.tokens ? P.tokens.length : 0})</span></div>
    <div>${P.tokens && P.tokens.length ? P.tokens.map((t) => `<span class="tag">${esc(t)}</span>`).join("") : "—"}</div>
    <div class="row" style="margin-top:4px;"><span>Content Tokens (No Stopwords)</span></div>
    <div>${P.without_stopwords && P.without_stopwords.length ? P.without_stopwords.map((t) => `<span class="tag">${esc(t)}</span>`).join("") : '<span class="muted">—</span>'}</div>
    <div class="row" style="margin-top:4px;"><span>Stemmed Representation</span></div>
    <div>${P.stems && P.stems.length ? P.stems.map((t) => `<span class="tag">${esc(t)}</span>`).join("") : '<span class="muted">—</span>'}</div>
  `;

  // 3. Sentiment Analysis & Polarity
  const S = r.sentiment || {};
  const sentLabel = S.label || "neutral";
  const sentCls = { positive: "pos", negative: "neg", neutral: "neu" }[sentLabel] || "neu";
  const sentEmoji = sentLabel === "positive" ? "😊" : sentLabel === "negative" ? "😔" : "😐";
  const compVal = Number.isFinite(S.compound) ? S.compound : 0;
  const compoundPercent = Math.max(0, Math.min(100, ((compVal + 1) / 2) * 100));

  const posVal = Number.isFinite(S.pos) ? S.pos : (Number.isFinite(S.scores?.pos) ? S.scores.pos : 0);
  const neuVal = Number.isFinite(S.neu) ? S.neu : (Number.isFinite(S.scores?.neu) ? S.scores.neu : 1);
  const negVal = Number.isFinite(S.neg) ? S.neg : (Number.isFinite(S.scores?.neg) ? S.scores.neg : 0);

  $("sentOut").innerHTML = `
    <div class="row" style="align-items:center;">
      <span>Classification</span>
      <span class="tag ${sentCls}" style="font-weight:600;font-size:12px;">${sentEmoji} ${esc(sentLabel.toUpperCase())}</span>
    </div>
    <div class="meter-wrapper">
      <div class="meter"><b style="left:${compoundPercent}%"></b></div>
      <div class="meter-ticks">
        <span>-1.0 Negative</span>
        <span>0.0 Neutral</span>
        <span>+1.0 Positive</span>
      </div>
    </div>
    <div class="row" style="margin-top:6px;">
      <span>Compound Score</span>
      <b>${compVal > 0 ? "+" + compVal.toFixed(2) : compVal.toFixed(2)}</b>
    </div>
    <div class="row">
      <span>Components</span>
      <span style="font-size:11px;">Pos: ${(posVal * 100).toFixed(0)}% · Neu: ${(neuVal * 100).toFixed(0)}% · Neg: ${(negVal * 100).toFixed(0)}%</span>
    </div>
    <div class="row">
      <span>Engine &amp; Negation</span>
      <span style="font-size:11px;">${esc(S.method || "multilingual")}${S.negated ? " (Negation Handled)" : ""}</span>
    </div>
  `;

  // 4. Intent Classification
  const I = r.intent;
  const intentRanked = I.ranked || [];
  const topConfidence = (I.confidence * 100).toFixed(0);

  let rankedHtml = "";
  if (intentRanked.length) {
    rankedHtml = intentRanked.slice(0, 3).map(([n, p]) => `
      <div class="row" style="font-size:12px;margin-top:2px;">
        <span>${esc(n.replace(/_/g, " "))}</span>
        <span>${(p * 100).toFixed(0)}%</span>
      </div>
      <div class="bar" style="height:4px;margin:1px 0 4px;"><i style="width:${Math.min(100, p * 100)}%"></i></div>
    `).join("");
  }

  $("intentOut").innerHTML = `
    <div class="row">
      <span>Predicted Intent</span>
      <b style="color:var(--emerald);font-size:14px;">${esc(I.name.replace(/_/g, " "))}</b>
    </div>
    <div class="row"><span>Confidence Score</span><b>${topConfidence}%</b></div>
    <div class="bar"><i style="width:${Math.min(100, topConfidence)}%"></i></div>
    <div style="margin-top:6px;font-size:11px;color:var(--muted);text-transform:uppercase;font-weight:600;">Top Ranked Alternatives</div>
    ${rankedHtml}
  `;

  // 5. Named Entity Recognition (NER)
  const entities = r.entities || [];
  const entityCategories = {
    PERSON: { title: "👤 Person Names", cls: "entity-person", items: [] },
    LOCATION: { title: "📍 Locations & Cities", cls: "entity-loc", items: [] },
    CITY: { title: "📍 Locations & Cities", cls: "entity-loc", items: [] },
    ORGANIZATION: { title: "🏢 Organizations", cls: "entity-org", items: [] },
    DATE: { title: "📅 Dates & Times", cls: "entity-date", items: [] },
    TIME: { title: "📅 Dates & Times", cls: "entity-date", items: [] },
    PHONE: { title: "📞 Contact & Communication", cls: "entity-contact", items: [] },
    EMAIL: { title: "📞 Contact & Communication", cls: "entity-contact", items: [] },
    MONEY: { title: "💰 Numeric & Monetary", cls: "entity-num", items: [] },
    NUMBER: { title: "💰 Numeric & Monetary", cls: "entity-num", items: [] },
    LANGUAGE: { title: "🌐 Languages", cls: "entity-person", items: [] },
  };

  for (const ent of entities) {
    const cat = entityCategories[ent.type];
    if (cat) {
      cat.items.push(ent.value);
    }
  }

  let entityHtml = "";
  let hasEntities = false;
  for (const [key, cat] of Object.entries(entityCategories)) {
    if (cat.items.length) {
      hasEntities = true;
      const uniqueItems = Array.from(new Set(cat.items));
      entityHtml += `
        <div class="entity-group">
          <div class="entity-group-title">${esc(cat.title)}</div>
          <div>${uniqueItems.map((v) => `<span class="tag ${cat.cls}">${esc(v)}</span>`).join("")}</div>
        </div>
      `;
    }
  }

  if (!hasEntities) {
    entityHtml = `<div class="muted" style="font-size:13px;padding:4px 0;">No named entities detected in this message.</div>`;
  }
  $("entitiesOut").innerHTML = entityHtml;

  // 6. Processing Latency & Engine Transparency
  const timing = r.timing || {};
  const localNlpMs = timing.local_nlp_ms || 0;
  const chatbotMs = timing.chatbot_ms || (r.reply && r.reply.latency_ms) || 0;
  const transMs = audioMeta && audioMeta.latency_ms ? audioMeta.latency_ms : 0;
  const totalMs = timing.total_ms || (localNlpMs + chatbotMs);

  const totalSum = (localNlpMs + chatbotMs + transMs) || 1;
  const nlpPct = Math.max(5, (localNlpMs / totalSum) * 100);
  const botPct = Math.max(10, (chatbotMs / totalSum) * 100);
  const transPct = transMs > 0 ? (transMs / totalSum) * 100 : 0;

  const engineName = r.reply && r.reply.engine ? r.reply.engine : "local rule";
  const modelName = r.reply && r.reply.model ? ` (${r.reply.model})` : "";

  $("latencyOut").innerHTML = `
    <div class="row">
      <span>Response Engine</span>
      <b>${esc(engineName)}${esc(modelName)}</b>
    </div>
    <div class="latency-bar">
      ${transMs > 0 ? `<div class="latency-segment trans" style="width:${transPct}%" title="Audio Transcription: ${transMs.toFixed(0)} ms"></div>` : ""}
      <div class="latency-segment nlp" style="width:${nlpPct}%" title="Local NLP Pipeline: ${localNlpMs.toFixed(1)} ms"></div>
      <div class="latency-segment bot" style="width:${botPct}%" title="Conversational Response: ${chatbotMs.toFixed(1)} ms"></div>
    </div>
    <div class="latency-legend">
      ${transMs > 0 ? `<span><i style="background:#f59e0b"></i> Audio STT: ${transMs.toFixed(0)} ms</span>` : ""}
      <span><i style="background:#3b82f6"></i> Local NLP: ${localNlpMs.toFixed(1)} ms</span>
      <span><i style="background:#10b981"></i> Chat Engine: ${chatbotMs >= 1000 ? (chatbotMs / 1000).toFixed(2) + "s" : chatbotMs.toFixed(0) + " ms"}</span>
    </div>
    <div class="row" style="margin-top:6px;border-top:1px dashed var(--line);padding-top:4px;">
      <span>Total Pipeline Latency</span>
      <b>⚡ ${totalMs >= 1000 ? (totalMs / 1000).toFixed(2) + "s" : totalMs.toFixed(0) + " ms"}</b>
    </div>
    ${clientTotalMs ? `<div class="row" style="font-size:11px;color:var(--muted);"><span>Client Turnaround (Network + Render)</span><span>${clientTotalMs.toFixed(0)} ms</span></div>` : ""}
  `;

  // 7. Translation & Speech Output
  const T = r.translation;
  $("transOut").innerHTML = `
    <div class="row">
      <span>Target Language</span>
      <b>${esc(T.target_name)}</b>
    </div>
    <div style="font-size:13px;background:var(--soft);padding:6px 10px;border-radius:8px;margin:4px 0;">
      ${T.ok ? esc(T.text) : '<span class="muted">Translation unavailable offline for this sentence.</span>'}
    </div>
    <div class="row" style="font-size:11px;color:var(--muted);">
      <span>Translation Engine</span>
      <span>${esc(T.engine || "Deep Translator")}</span>
    </div>
    <div class="row" style="font-size:11px;color:var(--muted);">
      <span>TTS Voice Target</span>
      <span>${esc(r.reply.tts || "en-IN")}</span>
    </div>
  `;

  // Update insight badge
  if ($("insightsBadge") && r.reply && r.reply.engine) {
    $("insightsBadge").style.display = "inline-block";
    const b = formatEngineBadge(r.reply.engine, r.reply.model);
    $("insightsBadge").textContent = b.text;
    $("insightsBadge").className = "badge " + b.cls;
  }
}

init();
