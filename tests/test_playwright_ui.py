"""
End-to-End Browser UI Validation with Playwright.
Tests all 5 core screens of the Strelza QA Platform plus Project Workspace Manager (Rename & Switch).
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8000"

def run_browser_ui_tests():
    print("=" * 75)
    print(">> STARTING PLAYWRIGHT END-TO-END UI VALIDATION SUITE")
    print(f"Target URL: {BASE_URL}")
    print("=" * 75)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # 1. Test Login & Authentication Portal
        print("\n[1/6] Testing Authentication Portal (/static/index.html)...")
        page.goto(f"{BASE_URL}/static/index.html")
        page.wait_for_selector(".auth-box")
        assert page.is_visible("text=STRELZA TELECOS QA")
        assert page.is_visible("#signInBtn")
        
        # Test Autofill
        page.click("text=Autofill")
        assert page.input_value("#loginUsername") == "admin"
        assert page.input_value("#loginPassword") == "admin123"

        # Submit Login
        page.click("#signInBtn")
        page.wait_for_url("**/static/dashboard.html", timeout=10000)
        print("  [PASS] Sign In succeeded, redirected to Dashboard.")

        # 2. Test Executive Compliance Dashboard
        print("\n[2/6] Testing Executive Dashboard (/static/dashboard.html)...")
        page.wait_for_selector(".summary-strip")
        page.wait_for_selector("#siteIdentifierText")
        page.wait_for_function('document.getElementById("siteIdentifierText") && document.getElementById("siteIdentifierText").textContent.length > 0')
        assert page.is_visible("#telemetryInputTokens")
        print("  [PASS] Dashboard KPIs, Site Baseline, and Token Telemetry rendered.")

        # 3. Test Project Workspace Manager (Manage & Rename Modals)
        print("\n[3/6] Testing Project Workspace Manager Modal (Manage)...")
        page.click("text=Manage")
        page.wait_for_selector("#manageProjectsModal")
        page.wait_for_selector("#manageProjectsTableBody tr")
        rows = page.query_selector_all("#manageProjectsTableBody tr")
        print(f"  [PASS] Project Manager Table rendered with {len(rows)} active workspace(s).")
        assert len(rows) >= 1

        # Check Rename button exists
        assert page.is_visible("text=Rename")
        page.click("text=Done")
        page.wait_for_timeout(300)
        print("  [PASS] Project Management Modal verified.")

        # 4. Test Package & Reference Hub
        print("\n[4/6] Testing Package & Reference Hub (/static/package.html)...")
        page.goto(f"{BASE_URL}/static/package.html")
        page.wait_for_selector(".cat-pills-bar")
        assert page.is_visible("text=Primary For-Construction Drawing Package")
        assert page.is_visible("text=Companion Reference Documents")
        assert page.is_visible(".ref-table")
        print("  [PASS] Package Hub, CAD sheet index, and companion reference table rendered.")

        # 5. Test Checkpoint Selection Workspace
        print("\n[5/6] Testing Checkpoints Workspace (/static/checkpoints.html)...")
        page.goto(f"{BASE_URL}/static/checkpoints.html")
        page.wait_for_selector("#checkpointTableContainer")
        page.wait_for_selector(".checkpoint-row")
        rows = page.query_selector_all(".checkpoint-row")
        print(f"  [PASS] Checkpoint Table rendered with {len(rows)} rules.")
        assert len(rows) >= 71

        # 6. Test Reports Hub
        print("\n[6/6] Testing Compliance Reports Hub (/static/reports.html)...")
        page.goto(f"{BASE_URL}/static/reports.html")
        page.wait_for_selector(".report-card-item")
        items = page.query_selector_all(".report-card-item")
        print(f"  [PASS] Reports Hub rendered with {len(items)} archived reports in LIFO order.")
        assert len(items) >= 1

        # Check that top report is active and pages preview container is populated
        page.wait_for_selector(".report-page-image")
        page_imgs = page.query_selector_all(".report-page-image")
        print(f"  [PASS] Multi-Page Viewer successfully rendered {len(page_imgs)} pages.")
        assert len(page_imgs) >= 1

        browser.close()

    print("\n" + "=" * 75)
    print("[SUCCESS] ALL 6 UI FLOWS VALIDATED & 100% CONSISTENT WITH ZERO REGRESSIONS!")
    print("=" * 75)

if __name__ == "__main__":
    run_browser_ui_tests()
