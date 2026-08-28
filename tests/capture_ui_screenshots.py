"""
Captures high-resolution browser verification screenshots using Playwright.
"""
import os
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\Dlux-user\.gemini\antigravity-ide\brain\cb4eefb3-e84d-4e66-9772-9f59d0f216b8"
BASE_URL = "http://localhost:8000"

def capture_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1366, "height": 850})
        page = context.new_page()

        # 1. Login
        page.goto(f"{BASE_URL}/static/index.html")
        page.wait_for_selector(".auth-box")
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "ui_login_verified.png"))

        # Autofill and login
        page.click("text=Autofill")
        page.click("#signInBtn")
        page.wait_for_url("**/static/dashboard.html")

        # 2. Dashboard
        page.wait_for_selector(".summary-strip")
        page.wait_for_timeout(400)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "ui_dashboard_verified.png"))

        # 3. Project Manager Modal
        page.click("text=Manage")
        page.wait_for_selector("#manageProjectsModal")
        page.wait_for_timeout(300)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "ui_project_manager_modal.png"))
        page.click("text=Done")

        # 4. Package Hub (Normal Table View)
        page.goto(f"{BASE_URL}/static/package.html")
        page.wait_for_selector(".ref-table")
        page.wait_for_selector(".ref-table tbody tr")
        page.wait_for_timeout(400)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "ui_package_table_high_contrast.png"))

        # 5. Package Hub with Toast Active
        page.evaluate('showToast("Primary drawing MD - MSV CHECK.pdf uploaded and indexed successfully.", true)')
        page.wait_for_selector(".upload-toast.show")
        page.wait_for_timeout(200)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "ui_package_toast_high_contrast.png"))

        # 6. Reports Hub
        page.goto(f"{BASE_URL}/static/reports.html")
        page.wait_for_selector(".report-page-image")
        page.wait_for_timeout(400)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "ui_reports_hub_verified.png"))

        browser.close()
    print("All high-contrast screenshots captured successfully.")

if __name__ == "__main__":
    capture_screenshots()
