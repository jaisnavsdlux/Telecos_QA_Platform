"""
Reports & Multi-Page Visualizer Router.
Serves compliance audit reports stack, high-resolution rendered pages, and PDF downloads.
"""
import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse

from backend.services.report_service import ReportService

router = APIRouter(tags=["Reports"])

@router.get("/api/reports")
def get_reports(project_id: Optional[str] = Query("H8097")):
    """Returns all available compliance reports in LIFO stack order (newest on top)."""
    return ReportService.scan_available_reports(project_id or "H8097")

@router.get("/api/projects/{project_id}/reports")
def get_project_reports(project_id: str):
    """Returns compliance reports for a specific project workspace."""
    return ReportService.scan_available_reports(project_id)

@router.get("/api/reports/{report_id}/view")
def view_report(report_id: str, project_id: Optional[str] = Query("H8097")):
    """Streams the PDF file for browser viewing."""
    fpath = ReportService.find_report_path(report_id, project_id or "H8097")
    if not fpath or not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Report PDF not found.")
    return FileResponse(fpath, media_type="application/pdf")

@router.get("/api/reports/{report_id}/download")
def download_report(report_id: str, project_id: Optional[str] = Query("H8097")):
    """Forces download of the PDF report file."""
    fpath = ReportService.find_report_path(report_id, project_id or "H8097")
    if not fpath or not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Report PDF not found.")
    fname = os.path.basename(fpath)
    return FileResponse(fpath, media_type="application/pdf", filename=fname)

@router.get("/api/reports/{report_id}/page/{page_num}")
def get_report_page_image(report_id: str, page_num: int, project_id: Optional[str] = Query("H8097")):
    """
    Renders a PDF page to PNG at 150 DPI.
    Executed synchronously in threadpool to prevent blocking the event loop.
    """
    fpath = ReportService.find_report_path(report_id, project_id or "H8097")
    if not fpath or not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Report PDF not found.")

    try:
        png_bytes = ReportService.render_page_png(fpath, page_num, dpi=150)
        return Response(content=png_bytes, media_type="image/png")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render page: {str(e)}")

@router.get("/download_latest_report")
def download_latest_report(project_id: Optional[str] = Query("H8097")):
    """Downloads the most recent report in the project stack."""
    reports = ReportService.scan_available_reports(project_id or "H8097")
    if not reports:
        raise HTTPException(status_code=404, detail="No compliance audit reports generated yet.")
    top = reports[0]
    return FileResponse(top["filepath"], media_type="application/pdf", filename=top["filename"])

@router.get("/report_full_package.pdf")
@router.get("/report.pdf")
def get_legacy_pdf():
    """Legacy compatibility endpoint."""
    fpath = "report_full_package.pdf"
    if not os.path.exists(fpath):
        fpath = "reports/H8097_Audit_Report_20260827_143131.pdf"
    if os.path.exists(fpath):
        return FileResponse(fpath, media_type="application/pdf")
    raise HTTPException(status_code=404, detail="Report not found.")
