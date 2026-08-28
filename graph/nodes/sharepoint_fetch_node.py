import os
from typing import Dict, Any
from graph.state_schema import GraphState


def sharepoint_fetch_node(state: GraphState) -> Dict[str, Any]:
    """
    Node: SharePoint Fetch
    Downloads the FC drawing list + Excel compliance checklist from SharePoint.
    In local-dev mode (no SP credentials), this node is a passthrough that
    expects pdf_path and excel_checklist_path to already be set in state.
    """
    job_id = state.get("job_id", "unknown")
    print(f"[sharepoint_fetch] Starting for job {job_id}")

    # ── Detect local-dev vs live SP ──────────────────────────────────────────
    sp_url = state.get("sharepoint_site_url", "")
    pdf_path = state.get("pdf_path", "")
    excel_path = state.get("excel_checklist_path", "")

    if not sp_url:
        # Local-dev: paths must already be provided in state
        print("[sharepoint_fetch] No SharePoint URL — running in local-dev passthrough mode.")
        if not pdf_path or not os.path.exists(pdf_path):
            return {"status": "failed", "error": f"[sharepoint_fetch] pdf_path not found: {pdf_path}"}
        return {
            "status": "fetched",
            "fc_drawing_list": [{"name": os.path.basename(pdf_path), "local_path": pdf_path}],
            "selected_fc_index": 0,
        }

    # ── Live SharePoint fetch (requires office365-rest-python-client) ─────────
    try:
        from office365.runtime.auth.client_credential import ClientCredential
        from office365.sharepoint.client_context import ClientContext

        client_id = os.getenv("SP_CLIENT_ID", "")
        client_secret = os.getenv("SP_CLIENT_SECRET", "")
        ctx = ClientContext(sp_url).with_credentials(ClientCredential(client_id, client_secret))

        # List FC PDFs from the configured library path
        sp_fc_library = os.getenv("SP_FC_LIBRARY", "Shared Documents/FC Drawings")
        folder = ctx.web.get_folder_by_server_relative_url(sp_fc_library)
        files = folder.files
        ctx.load(files)
        ctx.execute_query()

        fc_list = [{"name": f.properties["Name"], "url": f.properties["ServerRelativeUrl"]} for f in files]
        print(f"[sharepoint_fetch] Found {len(fc_list)} FC files in SharePoint.")

        return {
            "status": "fetched",
            "fc_drawing_list": fc_list,
        }

    except ImportError:
        return {"status": "failed", "error": "[sharepoint_fetch] office365-rest-python-client not installed. Run: pip install Office365-REST-Python-Client"}
    except Exception as e:
        return {"status": "failed", "error": f"[sharepoint_fetch] SharePoint error: {e}"}
