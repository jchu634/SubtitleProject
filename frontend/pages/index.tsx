import Image from "next/image";
import { Settings, Moon, Sun, Download, X } from "lucide-react";
import { useTheme } from "next-themes";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert"
import { toast } from "@/components/ui/use-toast";
import { Label } from "@/components/ui/label";

import React, { useState, useEffect, useRef } from "react";


declare global {
  interface Window {
    pywebview: {
      api: {
        killWindow: () => void;
        spawnSettingsWindow: () => void;
        killSettingsWindow: () => void;
        createToastOnMainWindow: (title: string, description: string, duration: number) => void;
        setWindowAlwaysOnTop: (alwaysOnTop: boolean) => void;
      };
    };
    createToast: (title: string, description: string, duration: number) => void;
  }
}


export default function Home() {

  const { setTheme } = useTheme()
  const [phrase, setPhrase] = useState("");
  const [transcription, setTranscription] = useState("");
  const [downloadButtonActive, setDownloadButtonActive] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [sseConnected, setSseConnected] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const sseSource = useRef<EventSource | null>(null);

  

  // useEffect(() => {
  //   if (typeof window !== 'undefined' && localStorage.getItem("settings") !== null) {
  //     const settings = JSON.parse(localStorage.getItem("settings") || "");
  //     if (settings.alwaysOnTop) {
  //       window.pywebview.api.setWindowAlwaysOnTop(true);
  //     }
  //   }
  // }, []);

  useEffect(() => {
    if (phrase && sseConnected){
      setTranscription((prevTranscription) => {
        const newTranscription = prevTranscription + "\n" + phrase;
        return newTranscription;
      });
    }
  }, [phrase])
  function startTranscribing(){
    if (localStorage.getItem("settings") !== null) {
      const settings = JSON.parse(localStorage.getItem("settings") || "");
      if (settings.transcriptionSource === "websocket") {
        startWebsocket();
      } else if (settings.transcriptionSource === "sse") {
        startSse();
      } else {
        console.error("No transcription source set, Falling back to websocket");
        startWebsocket();
      }
      setIsTranscribing(true);
      setTranscription(""); // Clear previous transcriptions
    }
  }
  function stopTranscribing(){
    if (localStorage.getItem("settings") !== null) {
      const settings = JSON.parse(localStorage.getItem("settings") || "");
      if (settings.transcriptionSource === "websocket") {
        stopWebsocket();
      } else if (settings.transcriptionSource === "sse") {
        stopSse();
      } else {
        console.error("No transcription source set, Falling back to websocket");
        stopWebsocket();
      }
      setIsTranscribing(false);
    }
  }
  function startSse() {
    if (sseConnected) {
      console.log("SSE already connected");
      return;
    }
    const sse = new EventSource("http://localhost:6789/transcription_feed_sse");
    
    // Event for each line of transcription
    sse.addEventListener("transcription_ready", function (event) {
      setPhrase(event.data);
    
      setTranscription((prevTranscription) => {
        const newTranscription = prevTranscription + "\n" + event.data;
        return newTranscription;
      });
    });
    
    // Currently broken
    // // Event when transcription phrase is complete
    // sse.addEventListener("phrase_complete", function (event) {
    //   setPhrase(event.data);
    // });
    
    // Event when Model is loaded and ready to transcribe
    sse.addEventListener("transcription", function (event) {
      setPhrase(event.data);
    });
    sseSource.current = sse;
    setSseConnected(true);
  }
  function startWebsocket() {
    if (wsConnected) {
      console.log("Websocket already connected");
      return;
    }
    const ws = new WebSocket("ws://localhost:6789/transcription_feed");
    ws.onopen = function(e) {
      console.log("Connected to server");
      setDownloadButtonActive(false);
    };
    ws.onmessage = function(event) {
      // console.log(event.data);
      if (event.data === "[PHRASE_COMPLETE]") {
        console.log("Phrase Acknowledged");
        // setTranscription(prevTranscription => {
        //   const updatedTranscription = [...prevTranscription, phrase];
        //   console.log("Updated Transcription" + updatedTranscription); // Log the updated transcription
        //   return updatedTranscription;
        // });

      } else {
        // Note: This is supposed to be run when the phrase is complete.
        // However, there is a bug in the backend which only acknowledges that the phrase is complete sometimes.
        // Therefore, this is run every time a new transcription is received.
        // #TODO: Remove this when the backend is fixed.
        setPhrase(event.data);
        setTranscription(prevTranscription => {
          const newTranscription = prevTranscription + "\n" + event.data;
          console.log("New Transcription: " + newTranscription);
          return newTranscription;
        });
      }
      ws.send("ack");
    };
    wsRef.current = ws;
    setWsConnected(true);
  }

  function stopSse(){
    if (!sseConnected) {
      console.log("SSE already disconnected");
      return;
    }
    if (sseSource.current) {
      sseSource.current.close();
      sseSource.current = null;
    }
    if (localStorage.getItem("settings") !== null) {
      const settings = JSON.parse(localStorage.getItem("settings") || "");
      if (settings.saveSubtitles) {
        downloadTranscription();
      }
    }
    setSseConnected(false);
    setDownloadButtonActive(true);
  }
  function stopWebsocket() {
    if (!wsConnected) {
      console.log("Websocket already disconnected");
      return;
    }
    if (wsRef.current) {
      // setTranscription(transcription + "\n" + phrase);
      wsRef.current.close(1000, "Closing connection Normally");
      wsRef.current = null;
    }
    if (localStorage.getItem("settings") !== null) {
      const settings = JSON.parse(localStorage.getItem("settings") || "");
      if (settings.saveSubtitles) {
        downloadTranscription();
      }
    }
    setWsConnected(false);
    setDownloadButtonActive(true);
  }
  
  
  function downloadTranscription() {
    const blob = new Blob([transcription], { type: 'text/plain' });
    console.log(transcription);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.download = 'transcription.txt';
    a.href = url;
    a.click();
    URL.revokeObjectURL(url);
    // document.body.removeChild(a);
  }
  
  function closeWindow(){
    window.pywebview.api.killWindow()
  }
  
  function openSettings(){
    window.pywebview.api.spawnSettingsWindow()
  }

  if (typeof window !== 'undefined') {
    window.createToast = (title: string, description: string, duration: number) => {
      toast({
        title: title,
        description: description,
        duration: duration,
      });
    };
  } else {
    console.error("Window object not available");
  }

  return (
    <main className="flex min-h-screen flex-col justify-normal p-10 space-y-4">
      <div className="flex justify-between w-full">
        <Label className="flex items-end">Ryzen AI Subtitles</Label>
        <Button onClick={closeWindow} size="icon" variant="ghost" className="">
          <X />
        </Button>
      </div>
      <div className="flex items-center"> 
        <Alert className="border-4">
          <AlertDescription>
            { phrase || "Transcription has not started yet." }
          </AlertDescription>
        </Alert>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon" className="ml-2 mr-2 border-2">
              <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">Toggle theme</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setTheme("light")}>
              Light
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme("dark")}>
              Dark
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme("system")}>
              System
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        
        <Button className="items-center sm:max-w-[50px]" size="icon" onClick={openSettings}>
          <Settings className="h-4 w-4"/>
        </Button>
      </div>
      <div className="flex items-center">
        { !isTranscribing ? (
          <Button onClick={startTranscribing} size="lg" className="mr-4">Start Transcribing</Button>
        ):(
          <Button variant="destructive" onClick={stopTranscribing} size="lg" className="mr-4">Stop Transcribing</Button>
        )}
        {downloadButtonActive ? (
          <Button size="lg" onClick={downloadTranscription}>
            <Download className="mr-2"/>
            Download Transcription
          </Button>
        ) : (
          <Button size="lg" disabled>
            <Download className="mr-2"/>
            Download Transcription
          </Button>
        )}
      </div>
      
      
    </main>
  );
}