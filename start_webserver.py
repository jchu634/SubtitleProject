"""App entry point."""
import uvicorn
from backend.init import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("start_webserver:app", reload=True, port=6789, host="0.0.0.0", log_config="log.ini")