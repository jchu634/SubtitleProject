import webview
import sys
import threading

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
    
    def setWindowAlwaysOnTop(self, value):
        print("Setting window on top")
        try:
            window.on_top = value
            print("Window is now on top")
        except Exception as e:
            print(e)

class Api():
    def __init__(self, settings_window=None):
        print(settings_window == None)
        self.settings_window = settings_window

    def log(self, value):
        print(value)

    def killWindow(self):
        if self.settings_window:
           self.settings_window.destroy()
           self.settings_window = None
        window.destroy()
    
    def spawnSettingsWindow(self):
        if self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None
        settingsApi = SettingsWindowApi()
        self.settings_window = webview.create_window("Settings", "http://localhost:3000/settings", width=470, height=395, frameless=True, js_api=settingsApi)
        settingsApi.setWindow(self.settings_window)

    def killSettingsWindow(self):
        if self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None

    def createToastOnMainWindow(self, title, message, duration):
        window.evaluate_js(f"createToast('{title}','{message}',{duration})")
    
    def setWindowAlwaysOnTop(self, value):
        print("Setting window on top")
        try:
            window.on_top = value
            print("Window is now on top")
        except Exception as e:
            print(e)
    

if __name__ == "__main__":
    webview.settings['ALLOW_DOWNLOADS'] = True

    api_instance = Api()
    
    def on_closed():
        print("Main Window is Closed")
        try:
            print("Terminating Settings Window")
            api_instance.killSettingsWindow()
            
        except Exception as e:
            print(e)
    
    window = webview.create_window("Ryzen Transcription", "http://localhost:3000", width=700, height=295, frameless=True, js_api=api_instance)
    window.events.closed += on_closed

    webview.start(debug=True)
    sys.exit()
