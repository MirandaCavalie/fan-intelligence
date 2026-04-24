const state = {
  creator: "@lexfridman",
  fans: [],
  totalFans: 0,
  selected: null,
  eventSource: null,
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
  } catch {
    renderDetail(state.selected);
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

checkHealth();
loadFans().then(loadEvents).then(() => loadMemory());
setInterval(checkHealth, 7000);
setInterval(loadEvents, 5000);
