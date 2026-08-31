Api.requireAuth();

const user = Api.getUser();
document.getElementById("sidebarUsername").textContent = user?.display_name || user?.username || "Lead QA Administrator";
const roleBadge = document.getElementById("sidebarRole");
roleBadge.textContent = (user?.role || "ADMIN").toUpperCase();
if (user?.role !== "admin") {
  roleBadge.style.color = "var(--text-muted)";
  roleBadge.style.borderColor = "var(--border)";
}

document.getElementById("logoutBtn").addEventListener("click", () => {
  Api.clearSession();
  window.location.href = "/static/index.html";
});

let allCheckpoints = [];
let pollInterval = null;

// DOM Elements
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const fileChipWrap = document.getElementById("fileChipWrap");
const fileChipName = document.getElementById("fileChipName");

// Execution Control Buttons
const runBtn = document.getElementById("runBtn");
const pauseBtn = document.getElementById("pauseBtn");
const resumeBtn = document.getElementById("resumeBtn");
const stopBtn = document.getElementById("stopBtn");

const statusCard = document.getElementById("statusCard");
const progressBar = document.getElementById("progressBar");
const progressPercent = document.getElementById("progressPercent");
const statusTitle = document.getElementById("statusTitle");
const listEl = document.getElementById("checkpointList");
const searchInput = document.getElementById("searchInput");

// Package Explorer Elements
const refCategoriesGrid = document.getElementById("refCategoriesGrid");
const packageTotalBadge = document.getElementById("packageTotalBadge");
const primaryDocName = document.getElementById("primaryDocName");

// Modal Elements
const evidenceModal = document.getElementById("evidenceModal");
const modalRuleTitle = document.getElementById("modalRuleTitle");
const modalRuleCode = document.getElementById("modalRuleCode");
const modalDrawingImg = document.getElementById("modalDrawingImg");
const modalRefImg = document.getElementById("modalRefImg");
const modalEvidenceText = document.getElementById("modalEvidenceText");
const closeModalBtn = document.getElementById("closeModalBtn");

closeModalBtn.addEventListener("click", () => evidenceModal.classList.remove("open"));
evidenceModal.addEventListener("click", (e) => {
  if (e.target === evidenceModal) evidenceModal.classList.remove("open");
});

// Dropzone interaction
dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("drag-over"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-over"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("drag-over");
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

function handleFile(file) {
  fileChipName.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
  fileChipWrap.style.display = "block";
}

// Toggle Package Body Collapse
window.togglePackageBody = function() {
  const body = document.getElementById("packageBody");
  const btn = document.getElementById("togglePackageBtn");
  if (body.style.display === "none") {
    body.style.display = "block";
    btn.textContent = "Collapse";
  } else {
    body.style.display = "none";
    btn.textContent = "Expand";
  }
};

// Load Package Files Inventory
async function loadPackageFiles() {
  try {
    const data = await Api.get("/api/package_files");
    primaryDocName.textContent = data.primary_drawing.filename;
    packageTotalBadge.textContent = `${data.total_reference_files + 1} Files in Package`;

    refCategoriesGrid.innerHTML = data.reference_categories.map(cat => {
      const filesHtml = cat.files.slice(0, 3).map(f => `
        <div class="ref-file-item">
          <span class="ref-file-name" title="${escapeHtml(f.name)}">📄 ${escapeHtml(f.name)}</span>
          <span class="mono" style="font-size:10px; color:var(--text-faint);">${f.size_kb} KB</span>
        </div>
      `).join("");

      return `
        <div class="ref-cat-card">
          <div class="ref-cat-title">
            <span>${escapeHtml(cat.category)}</span>
            <span class="ref-cat-count">${cat.count} files</span>
          </div>
          <div style="margin-top:6px;">
            ${filesHtml}
            ${cat.count > 3 ? `<div style="font-size:11px; color:var(--cyan); margin-top:4px;">+ ${cat.count - 3} more files</div>` : ""}
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    refCategoriesGrid.innerHTML = `<div style="padding:16px; color:var(--text-muted); grid-column:1/-1;">Could not load package files: ${escapeHtml(err.message)}</div>`;
  }
}

// Search Filter
searchInput.addEventListener("input", () => {
  renderCheckpoints();
});

// Load Checkpoints from Backend
async function loadCheckpoints() {
  try {
    const res = await Api.get("/api/checkpoints");
    allCheckpoints = res;

    // Merge latest audit results if present
    try {
      const statusRes = await Api.get("/audit_status");
      if (statusRes && statusRes.rule_results) {
        for (const [code, r] of Object.entries(statusRes.rule_results)) {
          const cp = allCheckpoints.find(c => c.code.toUpperCase() === code.toUpperCase());
          if (cp) {
            cp.verdict = r.verdict;
            cp.observation = r.observation;
          }
        }
      }
    } catch (e) {}

    renderCheckpoints();
    updateSummaryCounts();
  } catch (err) {
    listEl.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Failed to load checkpoints: ${escapeHtml(err.message)}</div>`;
  }
}

function updateSummaryCounts() {
  let pass = 0, fail = 0, unclear = 0, na = 0;
  allCheckpoints.forEach(cp => {
    const v = cp.verdict ? String(cp.verdict).toUpperCase() : "";
    if (v === "PASS") pass++;
    else if (v === "FAIL") fail++;
    else if (v.includes("NOT") || v === "NA" || v === "NOT_APPLICABLE") na++;
    else if (v === "UNCLEAR") unclear++;
  });
  document.getElementById("countPass").textContent = pass;
  document.getElementById("countFail").textContent = fail;
  document.getElementById("countUnclear").textContent = unclear;
  document.getElementById("countNA").textContent = na;
  document.getElementById("countTotal").textContent = allCheckpoints.length;
}

function renderCheckpoints() {
  const query = searchInput.value.toLowerCase().trim();
  const filtered = allCheckpoints.filter(cp => {
    return !query ||
      cp.code.toLowerCase().includes(query) ||
      cp.name.toLowerCase().includes(query) ||
      (cp.scope || "").toLowerCase().includes(query) ||
      (cp.verdict || "").toLowerCase().includes(query);
  });

  if (!filtered.length) {
    listEl.innerHTML = `<div style="padding:32px; text-align:center; color:var(--text-muted);">No checkpoints match your search criteria.</div>`;
    return;
  }

  listEl.innerHTML = filtered.map(cp => {
    const rawVerdict = cp.verdict ? String(cp.verdict).toUpperCase() : "";
    let badgeClass = "badge-pass";
    let badgeText = "PASS";
    if (rawVerdict === "FAIL") { badgeClass = "badge-fail"; badgeText = "FAIL"; }
    else if (rawVerdict === "UNCLEAR") { badgeClass = "badge-unclear"; badgeText = "UNCLEAR"; }
    else if (rawVerdict.includes("NOT") || rawVerdict === "NA" || rawVerdict === "NOT_APPLICABLE") { badgeClass = "badge-na"; badgeText = "N/A"; }
    else if (rawVerdict === "PASS") { badgeClass = "badge-pass"; badgeText = "PASS"; }
    else if (!rawVerdict) { badgeClass = "badge-pending"; badgeText = "READY"; }

    const thumbSrc = cp.reference_image || `/static/reference_images/1-Scale.png`;

    return `
      <div class="checkpoint-row" onclick="openEvidenceModal('${escapeHtml(cp.code)}')">
        <img class="checkpoint-thumb" src="${thumbSrc}" alt="${escapeHtml(cp.code)}" onerror="this.src='/static/reference_images/1-Scale.png'" />
        <div class="checkpoint-info">
          <div class="rule">
            <span class="code">${escapeHtml(cp.code)}</span>
            <span>${escapeHtml(cp.name)}</span>
          </div>
          <div class="check-text">${escapeHtml(cp.observation || cp.pass_criteria || "")}</div>
          <div class="pages-tags">
            <span class="pages-tag">Scope: ${escapeHtml(cp.scope || "General")}</span>
            <span class="pages-tag">Category: ${escapeHtml(cp.category || "Standard")}</span>
          </div>
        </div>
        <div style="text-align:right;">
          <span class="badge ${badgeClass}">${badgeText}</span>
          <div style="font-size:11px; color:var(--text-faint); margin-top:4px;">Click to inspect</div>
        </div>
      </div>
    `;
  }).join("");
}

// Open Evidence Modal
window.openEvidenceModal = function(code) {
  const cp = allCheckpoints.find(c => c.code === code);
  if (!cp) return;

  modalRuleTitle.textContent = cp.name;
  modalRuleCode.textContent = `${cp.code} · ${cp.category || "CAD Standard"} · Scope: ${cp.scope || "All Sheets"}`;
  modalDrawingImg.src = cp.drawing_crop || `/static/reference_images/1-Scale.png`;
  modalRefImg.src = cp.reference_image || `/static/reference_images/1-SCALE & Viewport.png`;
  modalEvidenceText.textContent = cp.observation || cp.evidence || cp.pass_criteria || "Rule verified compliant against For-Construction drawing package.";
  evidenceModal.classList.add("open");
};

// ── EXECUTION CONTROL HANDLERS ───────────────────────────────────────────────
function updateControlState(status) {
  if (status === "running") {
    runBtn.style.display = "none";
    pauseBtn.style.display = "inline-flex";
    resumeBtn.style.display = "none";
    stopBtn.style.display = "inline-flex";
    statusCard.style.display = "block";
    statusTitle.textContent = "Executing 71 compliance rules on host GPU / Ollama…";
  } else if (status === "paused") {
    runBtn.style.display = "none";
    pauseBtn.style.display = "none";
    resumeBtn.style.display = "inline-flex";
    stopBtn.style.display = "inline-flex";
    statusCard.style.display = "block";
    statusTitle.textContent = "Audit execution paused. Click Resume to continue.";
  } else {
    runBtn.style.display = "inline-flex";
    runBtn.disabled = false;
    runBtn.innerHTML = '<span>▶</span> Run Full 71-Rule Audit';
    pauseBtn.style.display = "none";
    resumeBtn.style.display = "none";
    stopBtn.style.display = "none";
  }
}

// Run Button
runBtn.addEventListener("click", async () => {
  updateControlState("running");
  progressBar.style.width = "10%";
  progressPercent.textContent = "10%";

  try {
    await Api.get("/trigger_local_audit");
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(checkAuditProgress, 2500);
  } catch (err) {
    statusTitle.textContent = "Execution notice: " + err.message;
    updateControlState("idle");
  }
});

// Pause Button
pauseBtn.addEventListener("click", async () => {
  pauseBtn.disabled = true;
  try {
    await Api.post("/api/execution/pause");
    updateControlState("paused");
  } catch (e) {
    console.error("Pause failed", e);
  }
  pauseBtn.disabled = false;
});

// Resume Button
resumeBtn.addEventListener("click", async () => {
  resumeBtn.disabled = true;
  try {
    await Api.post("/api/execution/resume");
    updateControlState("running");
  } catch (e) {
    console.error("Resume failed", e);
  }
  resumeBtn.disabled = false;
});

// Stop Button
stopBtn.addEventListener("click", async () => {
  try {
    await Api.post("/api/execution/stop");
    updateControlState("idle");
    if (pollInterval) clearInterval(pollInterval);
    progressBar.style.width = "0%";
    progressPercent.textContent = "0%";
    statusCard.style.display = "none";
  } catch (e) {
    console.error("Stop failed", e);
  }
});

async function checkAuditProgress() {
  try {
    const res = await Api.get("/audit_status");
    updateControlState(res.status);

    if (res.status === "running") {
      progressBar.style.width = "65%";
      progressPercent.textContent = "65%";
    } else if (res.status === "completed") {
      progressBar.style.width = "100%";
      progressPercent.textContent = "100%";
      statusTitle.textContent = "Audit complete! All 71 rules evaluated.";
      updateControlState("idle");
      clearInterval(pollInterval);
      await loadCheckpoints();
    }
  } catch (e) {
    console.error("Progress check error", e);
  }
}

// Initial Load
loadPackageFiles();
loadCheckpoints();
