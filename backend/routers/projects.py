"""
Project & Workspace Management Router.
Handles project creation, updates/renames, deletions, drawing uploads, and reference ingestion.
"""
import os
import io
import shutil
import zipfile
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, status
from pydantic import BaseModel

from backend.services.project_service import ProjectService, classify_file

router = APIRouter(tags=["Projects & Workspaces"])

class ProjectCreate(BaseModel):
    id: str
    name: Optional[str] = ""
    structure_type: Optional[str] = "CONCRETE MONOPOLE (26.8m)"
    drawing_revision: Optional[str] = "FOR CONSTRUCTION (Rev 1.0)"

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    structure_type: Optional[str] = None
    drawing_revision: Optional[str] = None

@router.get("/api/projects")
def list_projects():
    """Returns all project workspaces with drawing status and file counts."""
    return ProjectService.list_all_projects()

@router.post("/api/projects")
def create_project(payload: ProjectCreate):
    """Creates a new isolated project workspace."""
    try:
        meta = ProjectService.create_project(
            project_id=payload.id,
            name=payload.name or payload.id,
            structure_type=payload.structure_type or "CONCRETE MONOPOLE (26.8m)",
            drawing_revision=payload.drawing_revision or "FOR CONSTRUCTION (Rev 1.0)"
        )
        return {"status": "success", "message": f"Project {payload.id} initialized.", "project": meta}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/projects/{project_id}")
def get_project_details(project_id: str):
    """Returns metadata and statistics for a specific project."""
    return ProjectService.get_project_meta(project_id)

@router.put("/api/projects/{project_id}")
@router.post("/api/projects/{project_id}/update")
def update_project(project_id: str, payload: ProjectUpdate):
    """Renames or updates configuration parameters of a project workspace."""
    try:
        updated = ProjectService.update_project(
            project_id=project_id,
            name=payload.name,
            structure_type=payload.structure_type,
            drawing_revision=payload.drawing_revision
        )
        return {"status": "success", "message": f"Project {project_id} updated.", "project": updated}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/api/projects/{project_id}")
@router.post("/api/projects/{project_id}/delete")
def delete_project(project_id: str):
    """Permanently deletes a project workspace and all its data (except baseline H8097)."""
    try:
        ProjectService.delete_project(project_id)
        return {"status": "success", "message": f"Project {project_id} permanently deleted."}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/projects/{project_id}/upload_drawing")
async def upload_project_drawing(project_id: str, file: UploadFile = File(...)):
    """Uploads and indexes the primary For-Construction drawing PDF for the project."""
    pdir = ProjectService.get_project_dir(project_id)
    dwg_dir = os.path.join(pdir, "drawing")
    os.makedirs(dwg_dir, exist_ok=True)

    fname = os.path.basename(file.filename or "drawing.pdf")
    dest_path = os.path.join(dwg_dir, fname)

    contents = await file.read()
    with open(dest_path, "wb") as out_f:
        out_f.write(contents)

    # Sync to Backblaze B2 under <project_id>/drawing/<filename>
    try:
        from backend.services.storage_service import storage
        storage.upload_project_file(project_id, "drawing", fname, contents, content_type="application/pdf")
    except Exception as e:
        print(f"[Upload] Notice syncing drawing to B2: {e}")

    # Parse sheets from the drawing PDF
    sheets = ProjectService.parse_pdf_sheets(dest_path)
    sheet_strings = [f"Sheet {s['sheet']}: {s['title']}" for s in sheets]

    # Update metadata
    meta = ProjectService.get_project_meta(project_id)
    meta["primary_drawing"] = fname
    meta["sheets"] = sheet_strings
    ProjectService.save_project_meta(project_id, meta)

    return {
        "status": "success",
        "message": f"Primary drawing {fname} uploaded and indexed successfully.",
        "primary_drawing": fname,
        "sheets_detected": sheets
    }

@router.post("/api/projects/{project_id}/upload_references")
async def upload_references(project_id: str, files: List[UploadFile] = File(...)):
    """
    Uploads companion reference files or folders for a specific project.
    Automatically detects if an uploaded PDF is an FC Drawing and indexes it into drawing/.
    Streams files directly to Backblaze B2 under <project_id>/references/.
    """
    pdir = ProjectService.get_project_dir(project_id)
    ref_dir = os.path.join(pdir, "references")
    dwg_dir = os.path.join(pdir, "drawing")
    os.makedirs(ref_dir, exist_ok=True)
    os.makedirs(dwg_dir, exist_ok=True)

    saved_files = []
    primary_dwg_detected = None
    from backend.services.storage_service import storage

    for f in files:
        fname = os.path.basename(f.filename or "file")
        if not fname:
            continue
        dest_path = os.path.join(ref_dir, fname)
        contents = await f.read()
        with open(dest_path, "wb") as out_f:
            out_f.write(contents)
        
        # Stream file to Backblaze B2 under <project_id>/references/<fname>
        try:
            c_type = "application/pdf" if fname.lower().endswith(".pdf") else "application/octet-stream"
            storage.upload_project_file(project_id, "references", fname, contents, content_type=c_type)
        except Exception as e:
            print(f"[Upload] Notice syncing reference to B2: {e}")

        saved_files.append({
            "name": fname,
            "size_kb": round(len(contents) / 1024, 1),
            "category": classify_file(fname)
        })

        # Check if file is an FC CAD drawing
        if fname.lower().endswith(".pdf") and (classify_file(fname) == "FC_Drawing" or len(files) == 1):
            shutil.copy2(dest_path, os.path.join(dwg_dir, fname))
            primary_dwg_detected = fname
            try:
                storage.upload_project_file(project_id, "drawing", fname, contents, content_type="application/pdf")
            except Exception:
                pass

        # Handle zip archives
        if fname.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(contents)) as z:
                    z.extractall(ref_dir)
                    # Check extracted files for drawings
                    for member in z.namelist():
                        if member.lower().endswith(".pdf") and classify_file(member) == "FC_Drawing":
                            ext_path = os.path.join(ref_dir, member)
                            if os.path.isfile(ext_path):
                                base_m = os.path.basename(member)
                                shutil.copy2(ext_path, os.path.join(dwg_dir, base_m))
                                primary_dwg_detected = base_m
            except Exception:
                pass

    # If an FC drawing was ingested, update project metadata
    if primary_dwg_detected:
        dwg_path = os.path.join(dwg_dir, primary_dwg_detected)
        sheets = ProjectService.parse_pdf_sheets(dwg_path)
        meta = ProjectService.get_project_meta(project_id)
        meta["primary_drawing"] = primary_dwg_detected
        meta["sheets"] = [f"Sheet {s['sheet']}: {s['title']}" for s in sheets]
        ProjectService.save_project_meta(project_id, meta)

    total_count = sum(len(f_list) for _, _, f_list in os.walk(ref_dir))
    return {
        "status": "success",
        "message": f"Successfully imported and indexed {len(saved_files)} document(s) in project {project_id}.",
        "uploaded_files": saved_files,
        "total_references": total_count,
        "primary_drawing_updated": primary_dwg_detected is not None
    }

@router.get("/api/package_files")
def get_package_files(project_id: Optional[str] = Query("H8097")):
    """Returns package files and companion references for the active project."""
    return ProjectService.get_package_files(project_id or "H8097")

@router.get("/api/projects/{project_id}/package_files")
def get_project_package_files(project_id: str):
    """Returns package files for a specific project."""
    return ProjectService.get_package_files(project_id)
