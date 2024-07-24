from init import create_app

import webview
import sys
import threading
import uvicorn

app = create_app()
def start_server():
    uvicorn.run(app, port=6789)

if __name__ == "__main__":
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    webview.create_window("Ryzen Transcription", "http://localhost:6789", width=800, height=400, frameless=True)
    webview.start()
    sys.exit()