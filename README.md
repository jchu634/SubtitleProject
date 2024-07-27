# Subtitle Project
This is a project for a windows GUI application for subtitling system audio in soft real-time using Whisper running on Ryzen AI.

## Setup + Installation
1. Clone the repository
2. Build the frontend
    ```powershell
    .\buildFrontend.ps1
    ```
3. Install all backend dependencies
    Instruction in Backend [README](./backend/README.md#installation)
4. Run the GUI
    ```powershell
    cd .\backend
    python start_gui.py
    ```

## Known Issues
#### Language Limitations:
- The application is currently unable to transcribe audio in any language other than English due to model limitations.

#### Subtitle Transcription Accuracy: 
- The subtitle transcription for speaker loopback inputs is less accurate compared to direct microphone inputs.

#### Performance Issue After Stopping Transcription:
- After clicking Stop Transcription, the application may become very slow due to ongoing backend transcription jobs. The application will return to normal speed after a short delay.
- Note: The download subtitles button remains functional and works independently of the backend.

#### Stability Issues:
- The application may crash if the user opens the settings window, selects the "Pin window to always stay on top" option, and then closes the settings window to quickly. (i.e. <2 seconds)
    - This happens as the settings window has not been able to load the Settings javascript-python api bridge before it is closed.
    - This issue can be mitigated by waiting at least 3 seconds after selecting the "Pin window to always stay on top" option before closing the settings window.