from config import Settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app():
    tags_metadata = [
        {
            "name": "Utilities",
            "description": "Contains functions for the frontend to interact with."
        },
        {
            "name": "Home",
            "description": "Api dedicated to serving the React App for local app client+server deployment."
        },
        {
            "name": "Transcription",
            "description": "Api dedicated for delivering the transcription to users"
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from home import home
    from utilities import sound, transcription
    from Whisper import transcription_server
    
    app.include_router(sound.utils_api)
    app.include_router(transcription.utils_api)
    app.include_router(transcription_server.transcribe_api)

    # Always include the home router last as it contains a catch all route which will prevent other routes from being accessed
    app.include_router(home.home_router)
    return app