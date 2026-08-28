/**
 * Strelza QA Platform — Frontend Runtime Configuration
 * Automatically switches between local development backend and live Render production backend.
 */
window.APP_CONFIG = {
  // Replace with your live Render backend URL when deployed (e.g. "https://telecos-backend.onrender.com")
  API_BASE_URL: (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? "http://localhost:8000"
    : (window.location.origin.includes("vercel.app") 
        ? "https://telecos-backend.onrender.com"  // Set your Render backend domain here
        : window.location.origin)
};
