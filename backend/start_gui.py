from init import create_app

import webview
import sys
import threading
import uvicorn

app = create_app()
def start_server():
    uvicorn.run(app, port=6789)

class SettingsWindowApi():
    def __init__(self):
        self._window = None

    def log(self, value):
        print(value)

    def killSettingsWindow(self):
        self._window.destroy()
    
    def setWindow(self,window):
        self._window = window

    def createToastOnMainWindow(self, title, message, duration):
        window.evaluate_js(f"createToast('{title}','{message}',{duration})")

class Api():
    def __init__(self, settings_window=None):
        self.settings_window = settings_window

    def log(self, value):
        print(value)

    def killWindow(self):
        if self.settings_window:
           self.settings_window.destroy()
           self.settings_window = None
        window.destroy()
        sys.exit()
    
    def spawnSettingsWindow(self):
        if self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None
        settingsApi = SettingsWindowApi()
        self.settings_window = webview.create_window("Settings", "http://localhost:6789/settings", width=535, height=400, frameless=True, js_api=settingsApi)
        settingsApi.setWindow(self.settings_window)

    def killSettingsWindow(self):
        if self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None
    
    def createToastOnMainWindow(self, title, message, duration):
        window.evaluate_js(f"createToast('{title}','{message}',{duration})")

if __name__ == "__main__":
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    webview.settings['ALLOW_DOWNLOADS'] = True
    api_instance = Api()

    def on_closed():
        print("Main Window is Closed")
        try:
            print("Terminating Settings Window")
            api_instance.killSettingsWindow()            
        except Exception as e:
            print(e)
    
    window = webview.create_window("Ryzen Transcription", "http://localhost:6789", width=800, height=400, frameless=True, js_api=api_instance)
    window.events.closed += on_closed
    
    webview.start(debug=True)
    sys.exit()