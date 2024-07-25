import Image from "next/image";
import { Settings, Moon, Sun, Download, X } from "lucide-react";
import { useTheme } from "next-themes";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert"

import React, { useState, useEffect, useRef } from "react";

// Forms
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

// Fetching
import useSWR from "swr";

declare global {
  interface Window {
    pywebview: {
      api: {
        kill_window: () => void;
      };
    };
  }
}

const fetcher = (url: string) => fetch(url).then(r => r.json())

export function useDevices() {
  const { data, error, isLoading} = useSWR(
    'http://localhost:6789/api/sound_devices', 
    fetcher
  );
  if (error) return "An error has occurred.";
  if (isLoading) return "Loading...";
  return data;
}

function setDevices(index: number): Promise<boolean> {
  console.log("Setting device index to:", index);
  const fetchPromise = fetch('http://localhost:6789/api/sound_devices', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: index.toString(),
  })
  .then(response => {
    console.log('Response:', response);
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  })
  .then(data => {
    console.log('Device set successfully:', data);
    return true;
  })
  .catch(error => {
    console.error('Error setting device:', error);
    return false;
  });

  const timeoutPromise = new Promise<boolean>((resolve) => {
    setTimeout(() => {
      console.error('Fetch request timed out');
      resolve(false);
    }, 10000); // 10 seconds timeout
  });

  return Promise.race([fetchPromise, timeoutPromise]);
}


const SettingsFormSchema = z.object({
  device_index: z
    .number({ 
      required_error: "Please select sound-device"  
    })
    .int().nonnegative(),
  
  saveSubtitles: z.boolean(
    {
      required_error: "Please select an option to save subtitles",
    }
  ),
  
})

export default function Home() {
  let devices = useDevices()
  const { setTheme } = useTheme()
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const form = useForm<z.infer<typeof SettingsFormSchema>>({
    resolver: zodResolver(SettingsFormSchema),
    defaultValues: {
      device_index: 0,
      saveSubtitles: false,
    },
  });

  function onSubmit(values: z.infer<typeof SettingsFormSchema>) {
    setIsDialogOpen(false); // Close the dialog
    localStorage.setItem("settings", JSON.stringify(values));
    console.log('Saved settings:', values);
    setDevices(values.device_index)
    .then(set => {
      console.log(set);
      if (!set) {
        toast({
          title: "Error",
          description: "Error setting device",
          duration: 2000,
        });
      } else {
        toast({
          title: "Settings Saved",
          description: "Your settings have been set successfully.",
          duration: 2000,
        });
      }
    })
    .catch(error => {
      console.error('Error:', error);
      toast({
        title: "Error",
        description: "Error setting device, please try again later.",
        duration: 2000,
      });
    });
  }

  const [phrase, setPhrase] = useState("");
  const [transcription, setTranscription] = useState<string[]>([]);
  const [downloadButtonActive, setDownloadButtonActive] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  

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
      console.log(event.data);
      if (event.data === "[PHRASE_COMPLETE]") {
        setTranscription(prevTranscription => [...prevTranscription, phrase]);
      } else {
        setPhrase(event.data);
      }
      ws.send("ack");
    };
    wsRef.current = ws;
    setWsConnected(true);
  }

  function stopWebsocket() {
    if (!wsConnected) {
      console.log("Websocket already disconnected");
      return;
    }
    if (wsRef.current) {
      setTranscription(prevTranscription => [...prevTranscription, phrase]);
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
    const blob = new Blob(transcription, { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.download = 'transcription.txt';
    a.href = url;
    a.click();
    URL.revokeObjectURL(url);
    // document.body.removeChild(a);
  }
  
  function closeWindow(){
    window.pywebview.api.kill_window()
  }

  return (
    <main className="flex min-h-screen flex-col justify-normal p-24 space-y-4">
      <div className="flex justify-end w-full">
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
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="items-center sm:max-w-[50px]" size="icon" onClick={() => setIsDialogOpen(true)}>
              {/* Settings  */}
              <Settings className="h-4 w-4"/>
            </Button>
          </DialogTrigger>

          <DialogContent className="sm:max-w-[450px]">
            <DialogHeader>
              <DialogTitle>Settings</DialogTitle>
              <DialogDescription>
                Make changes to your settings here<br/>Click save when you&apos;re done.
              </DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)}>
                <div className="grid gap-4 py-2">
                  <FormField
                    control={form.control}
                    name="device_index"
                    render={({ field }) => (
                      <FormItem>
                        <Controller
                          control={form.control}
                          name="device_index"
                          render={({ field }) => (
                              <Select onValueChange={(value) => field.onChange(parseInt(value))} value={field.value.toString()}>
                              <SelectTrigger className="w-[400px]">
                                <SelectValue placeholder="Choose a sound input device" />
                              </SelectTrigger>
                              <SelectContent>
                                {Array.isArray(devices) && devices.map((device: any) => (
                                  <SelectItem key={device.index} value={device.index.toString()}>
                                    {device.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        />
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={form.control}
                    name="saveSubtitles"
                    render={({ field }) => (
                      <FormItem>
                        <div className="flex items-center space-x-2">
                          <label
                            htmlFor="save"
                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                          >
                            Download Transcription automatically after recording.
                          </label>
                          <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <DialogFooter>
                  <Button type="submit" className="mt-4">Save changes</Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>
      <div className="flex items-center">
        { !wsConnected ? (
          <Button onClick={startWebsocket} size="lg" className="mr-4">Start Websocket</Button>
        ):(
          <Button variant="destructive" onClick={stopWebsocket} size="lg" className="mr-4">Stop Websocket</Button>
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