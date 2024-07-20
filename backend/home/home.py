from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
import os

home_router = APIRouter(tags=["Home"])
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

####### favicon #######
@home_router.get("/favicon.ico", responses={200: {"description": "Success"}, 404: {"description": "Not Found"}})
def favicon():
    """
        Serves the favicon
    """
    if os.path.exists(os.path.join(frontend_path,"static/favicon.ico")):
        return FileResponse(os.path.join(frontend_path,"static/favicon.ico"))
    else:
        return ORJSONResponse(content={"error": "File not found"}, status_code=404)


####### NextJS Build + Static #######
@home_router.get("/")
@home_router.get("/{path:path}", responses={200: {"description": "Success"}, 404: {"description": "Not Found"}})
def home(request: Request, path: str=None):
    """
        Serves the NextJS Frontend
    """     
    static_file_path = os.path.join(frontend_path, path)
    print(frontend_path)
    print(static_file_path)

    # Check if static file is a js, css or svg file (To prevent leaking other files)
    if static_file_path.endswith(".js") or static_file_path.endswith(".css") or static_file_path.endswith(".svg"):
        # Checks if Static file exists
        if os.path.isfile(static_file_path):
            return FileResponse(static_file_path)    
    
    if static_file_path.endswith(".html"):
        # Check if frontend exists
        return HTMLResponse(open(static_file_path, "r").read())
    
    # Check if frontend exists
    if os.path.exists(os.path.join(frontend_path, "index.html")):
        return HTMLResponse(open(os.path.join(frontend_path, "index.html"), "r").read())
    return ORJSONResponse(content={"error": "Frontend not found"}, status_code=404)