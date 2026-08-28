Api.requireAuth();

const user = Api.getUser();
document.getElementById("sidebarUsername").textContent = user?.display_name || user?.username || "Lead QA Engineer";
document.getElementById("sidebarRole").textContent = (user?.role || "ADMIN").toUpperCase();

document.getElementById("logoutBtn").addEventListener("click", () => {
  Api.clearSession();
  window.location.href = "/static/index.html";
});
