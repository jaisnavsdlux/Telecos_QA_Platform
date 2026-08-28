Api.requireAuth();

const user = Api.getUser();
document.getElementById("sidebarUsername").textContent = user?.display_name || user?.username || "Lead QA Engineer";
document.getElementById("sidebarRole").textContent = (user?.role || "ADMIN").toUpperCase();

document.getElementById("logoutBtn").addEventListener("click", () => {
  Api.clearSession();
  window.location.href = "/static/index.html";
});

const listEl = document.getElementById("adminList");
const searchInput = document.getElementById("adminSearch");
let checkpoints = [];

async function load() {
  try {
    checkpoints = await Api.get("/api/checkpoints");
    render();
  } catch (e) {
    listEl.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Failed to load rule definitions: ${escapeHtml(e.message)}</div>`;
  }
}

function render() {
  const q = searchInput.value.toLowerCase().trim();
  const filtered = checkpoints.filter(c => {
    return !q || c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q) || (c.category || "").toLowerCase().includes(q);
  });

  if (!filtered.length) {
    listEl.innerHTML = `<div style="padding:32px; text-align:center; color:var(--text-muted);">No checkpoints found matching filter.</div>`;
    return;
  }

  listEl.innerHTML = filtered.map(c => `
    <div class="checkpoint-row" style="padding-left:20px; padding-right:20px;">
      <img class="checkpoint-thumb" src="${c.reference_image || '/static/reference_images/1-Scale.png'}" alt="" onerror="this.src='/static/reference_images/1-Scale.png'" />
      <div class="checkpoint-info">
        <div class="rule">
          <span class="code">${escapeHtml(c.code)}</span>
          <span>${escapeHtml(c.name)}</span>
        </div>
        <div class="check-text"><strong>Pass Criteria:</strong> ${escapeHtml(c.pass_criteria || c.description || "")}</div>
        <div class="pages-tags">
          <span class="pages-tag">Scope: ${escapeHtml(c.scope || "General")}</span>
          <span class="pages-tag">Category: ${escapeHtml(c.category || "CAD Standard")}</span>
        </div>
      </div>
      <div class="checkpoint-actions">
        <span class="badge badge-pass">ACTIVE</span>
      </div>
    </div>
  `).join("");
}

searchInput.addEventListener("input", render);
load();
