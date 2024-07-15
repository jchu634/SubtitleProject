from .config import Settings
from fastapi import FastAPI

def create_app():
    tags_metadata = [
        {
            "name": "Utilities",
            "description": "Core of the API. Contains functions that are designed for the frontend."
        },
        {
            "name": "Home",
            "description": "Api dedicated to serving the React App for local app client+server deployment."
        },
        {
            "name": "DEBUG",
            "description": "Debug API"
        }

    ]
    if Settings.ENV == "development":
        app = FastAPI(openapi_tags=tags_metadata)
    else:
        app = FastAPI(openapi_tags=tags_metadata, docs_url=None, redoc_url=None)

    # print(Settings.model_dump())

    from .home import home
    from .utilities import transcription
    
    app.include_router(transcription.utils_api)

    # Always include the home router last as it contains a catch all route which will prevent other routes from being accessed
    app.include_router(home.home_router)
    return app