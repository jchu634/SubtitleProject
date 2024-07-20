import Image from "next/image";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

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
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
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
    </main>
  );
}
