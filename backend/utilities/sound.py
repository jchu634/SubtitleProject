from fastapi import APIRouter, Request, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from config import Settings
import pyaudiowpatch as pyaudio


utils_api = APIRouter(tags=["Utilities"])

# For JSON format
class sound_device():
    def __init__(self, name: str, index:int, maxInputChannels: int, defaultSampleRate: int):
        self.name = name
        self.maxInputChannels = maxInputChannels
        self.defaultSampleRate = defaultSampleRate
        self.index = index
    

@utils_api.get("/api/get_sound_devices", responses={200: {"description": "Success"}, 404: {"description": "Not Found"}})
def get_sound_devices(request: Request):
    """
        Get all available sound devices
    """
    
    audio = pyaudio.PyAudio()
    devices = []
    try:
        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            device = sound_device(device_info["name"],i, device_info["maxInputChannels"], device_info["defaultSampleRate"])
            
            # A jank but effective way to remove the non-loopback device if a loopback device exists
            # The loopback device often has multiple duplicate entries, if a duplicate device is chosen, it doesn't work
            if "[Loopback]" in device.name:
                pop_list = []
                for j,dev in enumerate(devices):
                    if dev.name == device.name.split(" [Loopback]")[0]:
                        pop_list.append(j)
                for j in pop_list[::-1]:
                    devices.pop(j)    
            
            devices.append(device)

    except Exception as e:
        audio.terminate()
        return JSONResponse({"error": str(e)}, 500)
    
    else:
        devices = jsonable_encoder(devices)

    finally:
        audio.terminate()
        
    return JSONResponse(devices)

@utils_api.post("/api/set_sound_device", responses={200: {"description": "Success"}, 404: {"description": "Not Found"}})
def set_sound_device(request: Request, device_index: int = Body(...)):
    """
        Sets the sound device to use
    """
    try:
        Settings.SOUND_DEVICE = device_index
    except Exception as e:
        return JSONResponse({"error": str(e)}, 500)    
    return JSONResponse({"message": "Success"})