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
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useForm } from "react-hook-form";

async function getDevices() {
  const devices = await fetch('http://localhost:6789/api/get_sound_devices')
  if (!devices.ok){
    throw new Error('Failed to fetch devices')
  }
  return devices.json()
}

export default async function Home() {
  const devices = await getDevices()

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
              {devices.map((device: any) => (
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
          <Button 
            type="submit"
            onClick={(e: React.FormEvent) => {
              const saveSettings = () => {
               var settings = {
                sound_device: (document.getElementById('sound_device') as HTMLInputElement).value,
               } 
              }
              saveSettings()
              
            }
          >Save changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
      
      
    </main>
  );
}