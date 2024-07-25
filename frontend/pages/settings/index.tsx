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
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
  } from "@/components/ui/dialog"
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

  const form = useForm<z.infer<typeof SettingsFormSchema>>({
    resolver: zodResolver(SettingsFormSchema),
    defaultValues: {
      device_index: 0,
      saveSubtitles: false,
    },
  });

  function onSubmit(values: z.infer<typeof SettingsFormSchema>) {
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

  function closeSettingsWindow(){
    // window.pywebview.api.kill_settings_window()
    window.pywebview.api.kill_settings_window()
  }

  const [open, setOpen] = useState(true);

  useEffect(() => {
    if (!open) {
      closeSettingsWindow();
    }
  }, [open]);
  
  return (
    <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-[450px] min-h-80 flex flex-col">
            <DialogHeader>
                <DialogTitle className="text-left">Settings</DialogTitle>
                <DialogDescription className="text-left">
                    Make changes to your settings here<br />Click save when you&apos;re done.
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
                                    <FormLabel>Sound Input Device: </FormLabel>
                                    <Controller
                                    control={form.control}
                                    name="device_index"
                                    render={({ field }) => (
                                        <Select onValueChange={(value) => field.onChange(parseInt(value))} value={field.value.toString()}>
                                            
                                        <SelectTrigger className="w-[400px]">
                                            <SelectValue placeholder="Choose a sound input device" />
                                        </SelectTrigger>
                                        <SelectContent className="overflow-y-auto max-h-[10rem] max-w-[400px]">
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
                    <DialogFooter className="mt-[60px]">
                        <div className="flex justify-end">
                            <Button type="submit">Save changes</Button>
                        </div>
                    </DialogFooter>
                </form>
            </Form>
        </DialogContent>
    </Dialog>
  );
}