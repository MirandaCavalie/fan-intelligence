const state = {
  creator: "@lexfridman",
  fans: [],
  totalFans: 0,
  selected: null,
  eventSource: null,
  vapi: {
    client: null,
    sdkClass: null,
    config: null,
    active: false,
  },
};

const els = {
  form: document.querySelector("#scan-form"),
  creator: document.querySelector("#creator-input"),
  x: document.querySelector("#platform-x"),
  linkedin: document.querySelector("#platform-linkedin"),
  demo: document.querySelector("#demo-mode"),
  seed: document.querySelector("#seed-button"),
  health: document.querySelector("#health-pill"),
  scanStatus: document.querySelector("#scan-status"),
  eventStream: document.querySelector("#event-stream"),
  fanCount: document.querySelector("#fan-count"),
  leaderboard: document.querySelector("#leaderboard"),
  selectedScore: document.querySelector("#selected-score"),
  detail: document.querySelector("#fan-detail"),
  ask: document.querySelector("#ask-button"),
  publish: document.querySelector("#publish-button"),
  answer: document.querySelector("#vapi-answer"),
  publishStatus: document.querySelector("#publish-status"),
  publishLog: document.querySelector("#publish-log"),
  sponsorTrace: document.querySelector("#sponsor-trace"),
  memoryResults: document.querySelector("#memory-results"),
  voiceIntel: document.querySelector("#voice-intel-button"),
  voicePersona: document.querySelector("#voice-persona-button"),
  voiceEnd: document.querySelector("#voice-end-button"),
  voiceStatus: document.querySelector("#vapi-voice-status"),
  callPill: document.querySelector("#vapi-call-pill"),
  transcript: document.querySelector("#vapi-transcript"),
};

function normalizeHandle(value) {
  const trimmed = value.trim();
  if (!trimmed) return "@lexfridman";
  return trimmed.startsWith("@") ? trimmed : `@${trimmed}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function addEventRow(event) {
  const row = document.createElement("div");
  row.className = `event-row event-${event.type || "default"}`;
  const sponsor = event.sponsor || "faniq";
  const message = event.message || event.type || "event";
  row.innerHTML = `
    <div class="event-sponsor">${escapeHtml(sponsor)}</div>
    <div class="event-message">${escapeHtml(message)}</div>
  `;
  els.eventStream.prepend(row);
  while (els.eventStream.children.length > 35) {
    els.eventStream.lastElementChild.remove();
  }
}

function renderLeaderboard() {
  els.fanCount.textContent = `${state.totalFans || state.fans.length} fans`;
  if (!state.fans.length) {
    els.leaderboard.innerHTML = `<div class="empty">No fan data yet. Click Scan or load seed data.</div>`;
    renderDetail(null);
    return;
  }

  const maxScore = Math.max(...state.fans.map((fan) => fan.score), 1);
  els.leaderboard.innerHTML = state.fans
    .map((fan, index) => {
      const selected = state.selected?.handle === fan.handle ? "selected" : "";
      const width = Math.max(10, Math.round((fan.score / maxScore) * 100));
      const platforms = fan.platforms.map((platform) => `<div class="badge">${escapeHtml(platform)}</div>`).join("");
      return `
        <button class="fan-card ${selected}" data-handle="${escapeHtml(fan.handle)}">
          <div class="fan-rank">${index + 1}</div>
          <div class="fan-main">
            <div class="fan-title">
              <strong>${escapeHtml(fan.display_name)}</strong>
              <span>${escapeHtml(fan.handle)}</span>
            </div>
            <div class="score-track"><div style="width:${width}%"></div></div>
            <div class="fan-reason">${escapeHtml(fan.reason)}</div>
            <div class="badge-row">${platforms}<div class="badge source">${escapeHtml(fan.source_tool)}</div></div>
          </div>
          <div class="fan-score">${fan.score}</div>
        </button>
      `;
    })
    .join("");

  document.querySelectorAll(".fan-card").forEach((button) => {
    button.addEventListener("click", () => {
      const fan = state.fans.find((item) => item.handle === button.dataset.handle);
      state.selected = fan;
      renderLeaderboard();
      loadFanDetail(fan.handle);
    });
  });

  if (!state.selected) {
    state.selected = state.fans[0];
    loadFanDetail(state.selected.handle);
  }
}

async function loadFanDetail(handle) {
  if (!handle) return renderDetail(null);
  try {
    const response = await fetch(`/fan/${encodeURIComponent(state.creator)}/${encodeURIComponent(handle)}`);
    if (!response.ok) throw new Error("fan not found");
    const fan = await response.json();
    renderDetail(fan);
    await loadVapiConfig();
  } catch {
    renderDetail(state.selected);
    await loadVapiConfig();
  }
}

function renderDetail(fan) {
  if (!fan) {
    els.selectedScore.textContent = "No selection";
    els.detail.innerHTML = `<div class="empty">Select a fan to inspect comments, sources, and next action.</div>`;
    return;
  }

  els.selectedScore.textContent = `Score ${fan.score}`;
  const comments = (fan.raw_comments || []).slice(0, 3).map((comment) => `<li>${escapeHtml(comment)}</li>`).join("");
  const sources = (fan.source_urls || []).map((url) => `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(url)}</a>`).join("");
  els.detail.innerHTML = `
    <div class="detail-name">
      <strong>${escapeHtml(fan.display_name)}</strong>
      <span>${escapeHtml(fan.handle)}</span>
    </div>
    <p>${escapeHtml(fan.bio || "")}</p>
    <div class="detail-block">
      <div class="detail-label">Why this fan matters</div>
      <div>${escapeHtml(fan.reason || "")}</div>
    </div>
    <div class="detail-block">
      <div class="detail-label">Suggested action</div>
      <div>${escapeHtml(fan.suggested_action || "")}</div>
    </div>
    <div class="detail-block">
      <div class="detail-label">Engagement snippets</div>
      <ul>${comments}</ul>
    </div>
    <div class="detail-block sources">
      <div class="detail-label">Sources</div>
      ${sources || "No source links yet"}
    </div>
  `;
}

function setVoiceStatus(message, stateName = "idle") {
  els.voiceStatus.textContent = message;
  els.callPill.textContent = stateName;
  els.callPill.classList.toggle("live", stateName === "live");
  els.callPill.classList.toggle("warn", stateName === "setup" || stateName === "error");
}

function appendTranscript(role, text) {
  const current = els.transcript.textContent.includes("Voice transcript appears") ? "" : els.transcript.innerHTML;
  const row = `<div class="transcript-row"><strong>${escapeHtml(role || "vapi")}</strong><span>${escapeHtml(text || "")}</span></div>`;
  els.transcript.innerHTML = `${current}${row}`;
  els.transcript.scrollTop = els.transcript.scrollHeight;
}

async function loadVapiConfig() {
  state.creator = normalizeHandle(els.creator.value);
  const fanHandle = state.selected?.handle || "";
  try {
    const response = await fetch(
      `/vapi/client-config?creator_handle=${encodeURIComponent(state.creator)}&fan_handle=${encodeURIComponent(fanHandle)}`,
    );
    if (!response.ok) throw new Error("config unavailable");
    state.vapi.config = await response.json();
    if (state.vapi.config.configured) {
      setVoiceStatus("Ready for Vapi Web SDK", state.vapi.active ? "live" : "ready");
    } else {
      setVoiceStatus(`Setup needed: ${state.vapi.config.missing.join(", ")}`, "setup");
    }
  } catch {
    state.vapi.config = null;
    setVoiceStatus("Voice setup unavailable", "error");
  }
}

async function loadVapiSdk() {
  if (state.vapi.sdkClass) return state.vapi.sdkClass;
  try {
    const module = await import("https://esm.sh/@vapi-ai/web");
    state.vapi.sdkClass = module.default || module.Vapi;
    return state.vapi.sdkClass;
  } catch {
    setVoiceStatus("Could not load Vapi Web SDK; use typed Ask FanIQ fallback", "error");
    return null;
  }
}

function bindVapiEvents(client) {
  if (!client || client.__faniqBound || typeof client.on !== "function") return;
  client.__faniqBound = true;
  client.on("call-start", () => {
    state.vapi.active = true;
    setVoiceStatus("Vapi call live", "live");
  });
  client.on("call-end", () => {
    state.vapi.active = false;
    setVoiceStatus("Vapi call ended", "idle");
  });
  client.on("speech-start", () => setVoiceStatus("Vapi is speaking", "live"));
  client.on("speech-end", () => setVoiceStatus("Listening", "live"));
  client.on("message", (message) => {
    if (message?.type === "transcript" && message.transcript) {
      appendTranscript(message.role || "speaker", message.transcript);
    }
    if (message?.type === "model-output" && message.output) {
      appendTranscript("FanIQ", message.output);
    }
  });
  client.on("error", () => setVoiceStatus("Vapi call error; typed fallback still works", "error"));
}

async function ensureVapiClient() {
  await loadVapiConfig();
  const config = state.vapi.config;
  if (!config?.public_key) {
    setVoiceStatus("Add VAPI_PUBLIC_KEY before using browser voice", "setup");
    return null;
  }
  if (state.vapi.client) return state.vapi.client;
  const Vapi = await loadVapiSdk();
  if (!Vapi) return null;
  state.vapi.client = new Vapi(config.public_key);
  bindVapiEvents(state.vapi.client);
  return state.vapi.client;
}

async function startVapiCall(mode) {
  const client = await ensureVapiClient();
  if (!client) return;

  const config = state.vapi.config;
  const assistantId = mode === "persona" ? config.persona_assistant_id : config.intelligence_assistant_id;
  if (!assistantId) {
    const target = mode === "persona" ? "persona assistant" : "FanIQ Intelligence assistant";
    setVoiceStatus(`Missing ${target}; run scripts/setup_vapi.py`, "setup");
    return;
  }

  const label = mode === "persona" ? `persona ${state.selected?.handle || ""}` : "FanIQ Intelligence";
  els.transcript.innerHTML = "";
  appendTranscript("system", `Starting ${label}`);
  setVoiceStatus(`Starting ${label}`, "live");
  try {
    await client.start(assistantId);
  } catch {
    setVoiceStatus("Vapi start failed; typed Ask FanIQ fallback still works", "error");
  }
}

function endVapiCall() {
  if (state.vapi.client && typeof state.vapi.client.stop === "function") {
    state.vapi.client.stop();
  }
  state.vapi.active = false;
  setVoiceStatus("Voice call stopped", "idle");
}

async function loadFans() {
  state.creator = normalizeHandle(els.creator.value);
  let data;
  try {
    const response = await fetch(`/fans/${encodeURIComponent(state.creator)}?limit=15`);
    if (!response.ok) return;
    data = await response.json();
  } catch {
    return;
  }
  state.fans = data.top_fans || [];
  state.totalFans = data.total_fans || state.fans.length;
  if (state.selected && !state.fans.some((fan) => fan.handle === state.selected.handle)) {
    state.selected = null;
  }
  renderLeaderboard();
}

async function loadEvents() {
  let data;
  try {
    const response = await fetch(`/events/${encodeURIComponent(state.creator)}`);
    if (!response.ok) return;
    data = await response.json();
  } catch {
    return;
  }
  renderSponsorTrace(data.sponsor_trace || []);
  renderPublish(data.publish);
}

async function loadMemory(query = "AI research episode top fans") {
  let data;
  try {
    const response = await fetch(`/memory/${encodeURIComponent(state.creator)}/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) return;
    data = await response.json();
  } catch {
    return;
  }
  renderMemoryResults(data.results || []);
}

function renderSponsorTrace(trace) {
  if (!trace.length) {
    els.sponsorTrace.innerHTML = `<div class="empty">Sponsor operations appear here during scan, answer, and publish.</div>`;
    return;
  }
  els.sponsorTrace.innerHTML = trace
    .slice(0, 8)
    .map((row) => `
      <div class="trace-item">
        <strong>${escapeHtml(row.sponsor || "Sponsor")}</strong>
        <span>${escapeHtml(row.operation || "")}</span>
        <div>${escapeHtml(row.detail || "")}</div>
      </div>
    `)
    .join("");
}

function renderMemoryResults(results) {
  if (!results.length) {
    els.memoryResults.innerHTML = `<div class="empty">Redis memory snippets appear after fan comments are indexed.</div>`;
    return;
  }
  els.memoryResults.innerHTML = results
    .slice(0, 5)
    .map((row) => `
      <div class="trace-item memory-item">
        <strong>${escapeHtml(row.display_name || row.fan_handle)}</strong>
        <span>${escapeHtml((row.matched_terms || []).join(", ") || "context")}</span>
        <div>${escapeHtml(row.content || "")}</div>
      </div>
    `)
    .join("");
}

function renderPublish(publish) {
  if (!publish) {
    els.publishLog.innerHTML = `<div class="empty">No published report yet.</div>`;
    return;
  }
  els.publishStatus.textContent = `${publish.publisher} · ${publish.published_count} profiles`;
  els.publishLog.innerHTML = `
    <div class="trace-item">
      <strong>${escapeHtml(publish.publisher)}</strong>
      <span>${publish.payment_enabled ? "payment enabled" : "payment disabled"}</span>
      <div>${escapeHtml(publish.url)}</div>
    </div>
  `;
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    const health = await response.json();
    els.health.textContent = `${health.redis} · ${health.publisher}`;
    els.health.classList.toggle("degraded", health.redis !== "connected");
  } catch {
    els.health.textContent = "Offline";
    els.health.classList.add("degraded");
  }
}

async function startScan(event) {
  event.preventDefault();
  state.creator = normalizeHandle(els.creator.value);
  els.creator.value = state.creator;
  els.scanStatus.textContent = "Starting";
  els.eventStream.innerHTML = "";

  const platforms = [];
  if (els.x.checked) platforms.push("x");
  if (els.linkedin.checked) platforms.push("linkedin");

  const response = await fetch("/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      creator_handle: state.creator,
      platforms: platforms.length ? platforms : ["x"],
      demo_mode: els.demo.checked,
    }),
  });
  const job = await response.json();
  els.scanStatus.textContent = job.status;

  if (state.eventSource) state.eventSource.close();
  state.eventSource = new EventSource(`/scan/${job.job_id}`);
  state.eventSource.onmessage = async (message) => {
    const payload = JSON.parse(message.data);
    addEventRow(payload);
    if (["fan_found", "redis_write", "done"].includes(payload.type)) {
      await loadFans();
      await loadEvents();
    }
    if (payload.type === "done" || payload.type === "error") {
      els.scanStatus.textContent = payload.type === "done" ? "Done" : "Needs fallback";
      state.eventSource.close();
    }
  };
}

async function seedViaScan() {
  els.demo.checked = true;
  await startScan(new Event("submit"));
}

async function askFanIQ() {
  state.creator = normalizeHandle(els.creator.value);
  els.answer.textContent = "FanIQ is reading the Redis leaderboard...";
  const response = await fetch("/vapi/answer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "faniq-intelligence",
      metadata: { creator_handle: state.creator },
      messages: [{ role: "user", content: "Who are my top three fans and what should I do with them?" }],
    }),
  });
  const data = await response.json();
  els.answer.textContent = data.choices?.[0]?.message?.content || "No answer returned.";
  await loadMemory("Who are my top three fans and what should I do with them?");
  await loadEvents();
}

async function publishReport() {
  state.creator = normalizeHandle(els.creator.value);
  els.publishStatus.textContent = "Publishing";
  const response = await fetch(`/publish/${encodeURIComponent(state.creator)}`, { method: "POST" });
  const data = await response.json();
  renderPublish(data);
  await loadEvents();
}

els.form.addEventListener("submit", startScan);
els.seed.addEventListener("click", seedViaScan);
els.ask.addEventListener("click", askFanIQ);
els.publish.addEventListener("click", publishReport);
els.voiceIntel.addEventListener("click", () => startVapiCall("intelligence"));
els.voicePersona.addEventListener("click", () => startVapiCall("persona"));
els.voiceEnd.addEventListener("click", endVapiCall);

checkHealth();
loadFans().then(loadEvents).then(() => loadMemory()).then(() => loadVapiConfig());
setInterval(checkHealth, 7000);
setInterval(loadEvents, 5000);
