/**
 * Strelza Telecos Drawing QA Validator — Client API & Project Context Service
 * Strictly manages authentication, multi-project context, renaming, deletion, and API requests.
 */
const Api = (() => {
  const TOKEN_KEY = "strelza_token";
  const USER_KEY = "strelza_user";
  const ACTIVE_PROJECT_KEY = "strelza_active_project";

  function getToken() {
    return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY);
  }

  function getUser() {
    try {
      return JSON.parse(sessionStorage.getItem(USER_KEY) || localStorage.getItem(USER_KEY) || "null");
    } catch {
      return null;
    }
  }

  function setSession(token, user) {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  function clearSession() {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function requireAuth() {
    const token = getToken();
    const isAuthPage = window.location.pathname.endsWith("index.html") || window.location.pathname === "/";
    if (!token && !isAuthPage) {
      window.location.href = "/static/index.html";
    }
  }

  function getActiveProjectId() {
    return localStorage.getItem(ACTIVE_PROJECT_KEY) || "H8097";
  }

  function setActiveProjectId(id) {
    localStorage.setItem(ACTIVE_PROJECT_KEY, id);
    window.dispatchEvent(new CustomEvent("projectChanged", { detail: { projectId: id } }));
  }

  async function request(path, options = {}) {
    const token = getToken();
    const headers = options.headers || {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    
    // Auto append project_id query parameter if not present in path
    const activeProject = getActiveProjectId();
    let finalPath = path;
    if (!finalPath.includes("project_id=") && !finalPath.includes("/api/projects/") && !finalPath.includes("/api/auth/")) {
      const sep = finalPath.includes("?") ? "&" : "?";
      finalPath = `${finalPath}${sep}project_id=${encodeURIComponent(activeProject)}`;
    }

    // Support dynamic Vercel-to-Render remote backend URLs
    let baseUrl = (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) ? window.APP_CONFIG.API_BASE_URL.replace(/\/$/, '') : '';
    if (!baseUrl && (window.location.hostname.includes("vercel.app") || window.location.origin.includes("vercel.app"))) {
      baseUrl = "https://telecos-backend.onrender.com";
    }
    if (baseUrl && !finalPath.startsWith('http://') && !finalPath.startsWith('https://')) {
      finalPath = `${baseUrl}${finalPath.startsWith('/') ? '' : '/'}${finalPath}`;
    }

    if (options.json !== undefined) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(options.json);
    }

    const res = await fetch(finalPath, { ...options, headers });

    if (res.status === 401) {
      clearSession();
      window.location.href = "/static/index.html";
      throw new Error("Not authenticated");
    }

    if (!res.ok) {
      let errText = "Request failed (" + res.status + ")";
      try {
        const cloned = res.clone();
        const body = await cloned.json();
        errText = body.detail || body.message || errText;
      } catch {
        try {
          errText = await res.text();
        } catch (_) {}
      }
      throw new Error(errText);
    }

    const cType = res.headers.get("content-type") || "";
    if (cType.includes("application/json")) {
      return res.json();
    }
    return res.text();
  }

  return {
    getToken,
    getUser,
    setSession,
    clearSession,
    requireAuth,
    getActiveProjectId,
    setActiveProjectId,
    get: (path) => request(path, { method: "GET" }),
    post: (path, json) => request(path, { method: "POST", json }),
    put: (path, json) => request(path, { method: "PUT", json }),
    postForm: (path, formData) => request(path, { method: "POST", body: formData }),
    delete: (path) => request(path, { method: "DELETE" }),
  };
})();

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

let _onProjectSwitchCallback = null;

/**
 * Initializes the Global Project Selector in any UI container
 */
async function initProjectSelector(containerId, onSwitchCallback) {
  _onProjectSwitchCallback = onSwitchCallback;
  const container = document.getElementById(containerId);
  if (!container) return;

  try {
    const projects = await Api.get("/api/projects");
    const activeId = Api.getActiveProjectId();
    
    let html = `
      <div style="background:var(--surface-raised); border:1px solid var(--border); border-radius:var(--radius); padding:8px 12px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <span style="font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em;">Active Project</span>
          <div style="display:flex; gap:8px;">
            <button type="button" onclick="openNewProjectModal()" style="background:none; border:none; color:var(--cyan); font-size:11px; cursor:pointer; font-weight:600; padding:0;" title="Create new project workspace">+ New</button>
            <button type="button" onclick="openManageProjectsModal()" style="background:none; border:none; color:var(--text-muted); font-size:11px; cursor:pointer; font-weight:600; padding:0;" title="Rename, delete, or manage projects">⚙️ Manage</button>
          </div>
        </div>
        <select id="globalProjectSelect" style="width:100%; padding:7px 10px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm); color:var(--text); font-size:12px; font-weight:600; outline:none; cursor:pointer;">
          ${projects.map(p => `
            <option value="${escapeHtml(p.id)}" ${p.id === activeId ? 'selected' : ''}>
              📍 ${escapeHtml(p.code)} • ${escapeHtml(p.name)}
            </option>
          `).join("")}
        </select>
      </div>
    `;

    container.innerHTML = html;

    const selectEl = document.getElementById("globalProjectSelect");
    selectEl.addEventListener("change", (e) => {
      const chosenId = e.target.value;
      Api.setActiveProjectId(chosenId);
      if (onSwitchCallback) onSwitchCallback(chosenId);
      else window.location.reload();
    });

  } catch (err) {
    console.error("Failed to load projects", err);
  }
}

// ── New Project Modal ─────────────────────────────────────────
function injectProjectModals() {
  if (document.getElementById("newProjectModal")) return;

  const modalsHtml = `
    <!-- Create Project Modal -->
    <div id="newProjectModal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(15,23,42,0.6); backdrop-filter:blur(4px); z-index:9999; justify-content:center; align-items:center;">
      <div style="background:var(--surface); border:1px solid var(--border); border-top:3px solid var(--cyan); border-radius:var(--radius-lg); width:92%; max-width:480px; padding:24px; box-shadow:0 20px 40px rgba(0,0,0,0.15);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
          <h3 style="margin:0; font-size:17px; color:var(--text);">Create New Project Workspace</h3>
          <button type="button" onclick="closeNewProjectModal()" style="background:none; border:none; color:var(--text-muted); font-size:20px; cursor:pointer;">&times;</button>
        </div>
        <p style="font-size:12px; color:var(--text-muted); margin:0 0 16px 0;">Initialize an isolated project repository for drawing validation, reference indexing, and compliance auditing.</p>

        <form id="createProjectForm">
          <div class="field" style="margin-bottom:12px;">
            <label style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px; font-weight:600;">
              <span>Site ID / Project Code</span>
              <span class="mono" style="color:var(--cyan); font-size:10px;">Required</span>
            </label>
            <input type="text" id="newSiteId" placeholder="e.g. S1212, N4088, B9021" style="width:100%; padding:9px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); color:var(--text); font-size:13px;" required />
          </div>

          <div class="field" style="margin-bottom:12px;">
            <label style="display:block; font-size:12px; margin-bottom:4px; font-weight:600;"><span>Site Name / Location</span></label>
            <input type="text" id="newSiteName" placeholder="e.g. Blacktown Rooftop, Sydney CBD" style="width:100%; padding:9px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); color:var(--text); font-size:13px;" required />
          </div>

          <div class="field" style="margin-bottom:12px;">
            <label style="display:block; font-size:12px; margin-bottom:4px; font-weight:600;"><span>Structure Type</span></label>
            <select id="newStructureType" style="width:100%; padding:9px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); color:var(--text); font-size:13px;">
              <option value="CONCRETE MONOPOLE (26.8m)" selected>CONCRETE MONOPOLE (26.8m)</option>
              <option value="ROOFTOP MOUNT">ROOFTOP MOUNT</option>
              <option value="SELF SUPPORTING LATTICE TOWER">SELF SUPPORTING LATTICE TOWER</option>
              <option value="GUYED MAST TOWER">GUYED MAST TOWER</option>
            </select>
          </div>

          <div class="field" style="margin-bottom:16px;">
            <label style="display:block; font-size:12px; margin-bottom:4px; font-weight:600;"><span>Primary For-Construction CAD PDF (Optional)</span></label>
            <input type="file" id="newDrawingFile" accept=".pdf,.dwg" style="width:100%; padding:8px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); color:var(--text); font-size:12px;" />
          </div>

          <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
            <button type="button" class="btn" style="background:var(--surface-raised);" onclick="closeNewProjectModal()">Cancel</button>
            <button type="submit" class="btn btn-primary" id="createProjectSubmitBtn">Create &amp; Switch</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Manage Projects Modal -->
    <div id="manageProjectsModal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(15,23,42,0.6); backdrop-filter:blur(4px); z-index:9999; justify-content:center; align-items:center;">
      <div style="background:var(--surface); border:1px solid var(--border); border-top:3px solid var(--cyan); border-radius:var(--radius-lg); width:94%; max-width:920px; max-height:88vh; display:flex; flex-direction:column; padding:24px; box-shadow:0 20px 40px rgba(0,0,0,0.15);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
          <div>
            <h3 style="margin:0; font-size:18px; color:var(--text);">Project Workspace Manager</h3>
            <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">Rename, switch, or delete project workspaces across the system.</div>
          </div>
          <div style="display:flex; gap:10px;">
            <button type="button" class="btn btn-sm btn-primary" onclick="openNewProjectModal()">+ Add Project</button>
            <button type="button" onclick="closeManageProjectsModal()" style="background:none; border:none; color:var(--text-muted); font-size:22px; cursor:pointer; line-height:1;">&times;</button>
          </div>
        </div>

        <div style="flex:1; overflow-y:auto; border:1px solid var(--border); border-radius:var(--radius); margin-bottom:16px;">
          <table style="width:100%; border-collapse:collapse; text-align:left; font-size:12px;">
            <thead>
              <tr style="background:var(--surface-raised); border-bottom:1px solid var(--border); color:var(--text-muted); text-transform:uppercase; font-size:10px; font-weight:700;">
                <th style="padding:10px 14px; width:20%;">Site ID</th>
                <th style="padding:10px 14px; width:20%;">Project Name</th>
                <th style="padding:10px 14px; width:18%;">Structure</th>
                <th style="padding:10px 14px; width:22%;">Drawing / Files</th>
                <th style="padding:10px 14px; width:20%; text-align:right;">Actions</th>
              </tr>
            </thead>
            <tbody id="manageProjectsTableBody">
              <tr><td colspan="5" style="padding:24px; text-align:center; color:var(--text-muted);">Loading projects…</td></tr>
            </tbody>
          </table>
        </div>

        <div style="display:flex; justify-content:flex-end;">
          <button type="button" class="btn" style="background:var(--surface-raised);" onclick="closeManageProjectsModal()">Done</button>
        </div>
      </div>
    </div>

    <!-- Rename Project Modal -->
    <div id="renameProjectModal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(15,23,42,0.65); backdrop-filter:blur(4px); z-index:10000; justify-content:center; align-items:center;">
      <div style="background:var(--surface); border:1px solid var(--border); border-top:3px solid var(--cyan); border-radius:var(--radius-lg); width:90%; max-width:440px; padding:22px; box-shadow:0 20px 40px rgba(0,0,0,0.2);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
          <h3 style="margin:0; font-size:16px; color:var(--text);">Rename / Edit Project</h3>
          <button type="button" onclick="closeRenameProjectModal()" style="background:none; border:none; color:var(--text-muted); font-size:20px; cursor:pointer;">&times;</button>
        </div>

        <form id="renameProjectForm">
          <input type="hidden" id="renameProjectId" />
          
          <div class="field" style="margin-bottom:12px;">
            <label style="display:block; font-size:12px; margin-bottom:4px; font-weight:600;">Site Identifier</label>
            <input type="text" id="renameSiteIdDisplay" disabled style="width:100%; padding:8px 12px; background:var(--surface-raised); border:1px solid var(--border); border-radius:var(--radius); color:var(--text-muted); font-family:var(--font-mono); font-size:13px; font-weight:700;" />
          </div>

          <div class="field" style="margin-bottom:12px;">
            <label style="display:block; font-size:12px; margin-bottom:4px; font-weight:600;">Site / Project Name</label>
            <input type="text" id="renameSiteName" required style="width:100%; padding:9px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); color:var(--text); font-size:13px;" />
          </div>

          <div class="field" style="margin-bottom:12px;">
            <label style="display:block; font-size:12px; margin-bottom:4px; font-weight:600;">Structure Type</label>
            <select id="renameStructureType" style="width:100%; padding:9px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); color:var(--text); font-size:13px;">
              <option value="CONCRETE MONOPOLE (26.8m)">CONCRETE MONOPOLE (26.8m)</option>
              <option value="ROOFTOP MOUNT">ROOFTOP MOUNT</option>
              <option value="SELF SUPPORTING LATTICE TOWER">SELF SUPPORTING LATTICE TOWER</option>
              <option value="GUYED MAST TOWER">GUYED MAST TOWER</option>
            </select>
          </div>

          <div class="field" style="margin-bottom:16px;">
            <label style="display:block; font-size:12px; margin-bottom:4px; font-weight:600;">Drawing Revision</label>
            <input type="text" id="renameDrawingRevision" style="width:100%; padding:9px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); color:var(--text); font-size:13px;" />
          </div>

          <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:18px;">
            <button type="button" class="btn" style="background:var(--surface-raised);" onclick="closeRenameProjectModal()">Cancel</button>
            <button type="submit" class="btn btn-primary" id="renameProjectSubmitBtn">Save Changes</button>
          </div>
        </form>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", modalsHtml);

  // Wire Create Project Submit
  document.getElementById("createProjectForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const siteId = document.getElementById("newSiteId").value.trim().toUpperCase();
    const siteName = document.getElementById("newSiteName").value.trim();
    const structType = document.getElementById("newStructureType").value;
    const drawingFileInput = document.getElementById("newDrawingFile");
    const btn = document.getElementById("createProjectSubmitBtn");

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Creating workspace…';

    try {
      await Api.post("/api/projects", {
        id: siteId,
        name: siteName,
        structure_type: structType
      });

      if (drawingFileInput.files && drawingFileInput.files[0]) {
        const formData = new FormData();
        formData.append("file", drawingFileInput.files[0]);
        await fetch(`/api/projects/${encodeURIComponent(siteId)}/upload_drawing`, {
          method: "POST",
          headers: { "Authorization": `Bearer ${Api.getToken()}` },
          body: formData
        });
      }

      Api.setActiveProjectId(siteId);
      closeNewProjectModal();
      window.location.reload();
    } catch (err) {
      alert("Failed to create project: " + err.message);
      btn.disabled = false;
      btn.innerHTML = "Create & Switch";
    }
  });

  // Wire Rename Project Submit
  document.getElementById("renameProjectForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const pid = document.getElementById("renameProjectId").value;
    const name = document.getElementById("renameSiteName").value.trim();
    const structure_type = document.getElementById("renameStructureType").value;
    const drawing_revision = document.getElementById("renameDrawingRevision").value.trim();
    const btn = document.getElementById("renameProjectSubmitBtn");

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Saving…';

    try {
      await Api.post(`/api/projects/${encodeURIComponent(pid)}/update`, {
        name,
        structure_type,
        drawing_revision
      });
      closeRenameProjectModal();
      await loadManageProjectsTable();
      initProjectSelector("projectSelectorContainer", _onProjectSwitchCallback);
      if (pid === Api.getActiveProjectId() && _onProjectSwitchCallback) {
        _onProjectSwitchCallback(pid);
      }
    } catch (err) {
      alert("Failed to rename project: " + err.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = "Save Changes";
    }
  });
}

function openNewProjectModal() {
  injectProjectModals();
  document.getElementById("newProjectModal").style.display = "flex";
  document.getElementById("newSiteId").focus();
}

function closeNewProjectModal() {
  const m = document.getElementById("newProjectModal");
  if (m) m.style.display = "none";
}

async function openManageProjectsModal() {
  injectProjectModals();
  document.getElementById("manageProjectsModal").style.display = "flex";
  await loadManageProjectsTable();
}

function closeManageProjectsModal() {
  const m = document.getElementById("manageProjectsModal");
  if (m) m.style.display = "none";
}

function openRenameProjectModal(pid, name, struct, rev) {
  injectProjectModals();
  document.getElementById("renameProjectId").value = pid;
  document.getElementById("renameSiteIdDisplay").value = pid;
  document.getElementById("renameSiteName").value = name || pid;
  document.getElementById("renameStructureType").value = struct || "CONCRETE MONOPOLE (26.8m)";
  document.getElementById("renameDrawingRevision").value = rev || "FOR CONSTRUCTION (Rev 1.0)";
  document.getElementById("renameProjectModal").style.display = "flex";
}

function closeRenameProjectModal() {
  const m = document.getElementById("renameProjectModal");
  if (m) m.style.display = "none";
}

async function loadManageProjectsTable() {
  const tbody = document.getElementById("manageProjectsTableBody");
  if (!tbody) return;

  try {
    const projects = await Api.get("/api/projects");
    const activeId = Api.getActiveProjectId();

    if (!projects.length) {
      tbody.innerHTML = `<tr><td colspan="5" style="padding:24px; text-align:center; color:var(--text-muted);">No projects found.</td></tr>`;
      return;
    }

    tbody.innerHTML = projects.map(p => {
      const isActive = p.id === activeId;
      const isBaseline = p.id === "H8097";
      return `
        <tr style="border-bottom:1px solid var(--border); ${isActive ? 'background:rgba(94,200,216,0.06);' : ''}">
          <td style="padding:12px 14px; font-weight:700; font-family:var(--font-mono);">
            <div style="display:flex; align-items:center; gap:6px;">
              <span>📍 ${escapeHtml(p.id)}</span>
              ${isActive ? '<span class="badge badge-pass" style="font-size:9px; padding:1px 5px;">ACTIVE</span>' : ''}
              ${isBaseline ? '<span class="badge" style="background:#e0f2fe; color:#0369a1; font-size:9px; padding:1px 5px;">BASELINE</span>' : ''}
            </div>
          </td>
          <td style="padding:12px 14px; font-weight:600; color:var(--text);">
            ${escapeHtml(p.name)}
          </td>
          <td style="padding:12px 14px; color:var(--text-muted); font-size:11px;">
            ${escapeHtml(p.structure_type)}
          </td>
          <td style="padding:12px 14px; font-size:11px;">
            <div style="color:var(--text); font-weight:500;">${escapeHtml(p.primary_drawing || 'No drawing')}</div>
            <div style="color:var(--text-muted); font-size:10px;">${p.reference_files_count || 0} references &bull; ${p.reports_count || 0} reports</div>
          </td>
          <td style="padding:12px 14px; text-align:right;">
            <div style="display:inline-flex; gap:6px;">
              ${!isActive ? `<button type="button" class="btn btn-sm btn-primary" onclick="activateProject('${escapeHtml(p.id)}')">Switch</button>` : ''}
              <button type="button" class="btn btn-sm" style="background:var(--surface-raised);" onclick="openRenameProjectModal('${escapeHtml(p.id)}', '${escapeHtml(p.name)}', '${escapeHtml(p.structure_type)}', '${escapeHtml(p.drawing_revision)}')">✏️ Rename</button>
              ${!isBaseline ? `
                <button type="button" class="btn btn-sm btn-danger" onclick="deleteProjectById('${escapeHtml(p.id)}')">🗑️ Delete</button>
              ` : `
                <button type="button" class="btn btn-sm" style="opacity:0.4; cursor:not-allowed;" title="Baseline project is protected">🔒</button>
              `}
            </div>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="padding:20px; text-align:center; color:var(--fail);">Failed to load projects: ${escapeHtml(err.message)}</td></tr>`;
  }
}

async function activateProject(pid) {
  Api.setActiveProjectId(pid);
  closeManageProjectsModal();
  initProjectSelector("projectSelectorContainer", _onProjectSwitchCallback);
  if (_onProjectSwitchCallback) {
    _onProjectSwitchCallback(pid);
  } else {
    window.location.reload();
  }
}

async function deleteProjectById(pid) {
  if (!confirm(`Are you sure you want to permanently delete project workspace "${pid}" and all its uploaded drawings and reports?\n\nThis action cannot be undone.`)) {
    return;
  }

  try {
    await Api.post(`/api/projects/${encodeURIComponent(pid)}/delete`);
    if (Api.getActiveProjectId() === pid) {
      Api.setActiveProjectId("H8097");
    }
    await loadManageProjectsTable();
    initProjectSelector("projectSelectorContainer", _onProjectSwitchCallback);
    if (_onProjectSwitchCallback) {
      _onProjectSwitchCallback(Api.getActiveProjectId());
    } else {
      window.location.reload();
    }
  } catch (err) {
    alert("Failed to delete project: " + err.message);
  }
}

// Auto-inject modals on DOM load
document.addEventListener("DOMContentLoaded", () => {
  injectProjectModals();
});
