import Image from "next/image";
import { Settings } from "lucide-react";
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
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { useForm } from "react-hook-form";
import { toast } from "@/components/ui/use-toast";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { useState, useEffect } from "react";
import React from "react";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then(r => r.json())

export function getDevices() {
  const { data, error, isLoading} = useSWR(
    'http://localhost:6789/api/get_sound_devices', 
    fetcher
  );
  if (error) return "An error has occurred.";
  if (isLoading) return "Loading...";
  return data;
}

// const FormSchema = z.object({
//   device_index: z
//     .number({ 
//       required_error: "Please select sound-device"  
//     })
//     .int().nonnegative(),
    
//   email: z
//     .string({
//       required_error: "Please select an email to display.",
//     })
//     .email(),
// })

export default function Home() {
  let devices = getDevices()
  
  console.log(devices)
  console.log(devices[0])
  console.log(typeof(devices))

  return (
    <main className="flex min-h-screen flex-col justify-between p-24">
     
      <Dialog>
      <DialogTrigger asChild>
        <Button className="items-center sm:max-w-[150px]">
          Settings 
          <Settings className="ml-2 h-4 w-4"/>
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-[450px]">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Make changes to your settings here<br/>Click save when you're done.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">

          <Select>
            
            <SelectTrigger className="w-[400px]">
              <SelectValue placeholder="Choose a sound input device" />
            </SelectTrigger>
            
            <SelectContent>
              {/* {devices.map((device: any) => (
                <SelectItem key={device.index} value={device.index}>{device.name}</SelectItem>
                ))} */}
              {Array.isArray(devices) && devices.map((device: any) => (
                <SelectItem key={device.index} value={device.index}>{device.name}</SelectItem>
              ))}
            </SelectContent>

          </Select>
          
          <div className="flex items-center space-x-2">
            <Checkbox id="save" />
            <label
              htmlFor="save"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Save Transcription after recording.
            </label>
          </div>

        </div>
              
            
        <DialogFooter>
          <Button type="submit">Save changes</Button>
        </DialogFooter>
      </DialogContent>
        
      </Dialog>
              
      
      
    </main>
  );
}
