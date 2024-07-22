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
import { toast } from "@/components/ui/use-toast";
import { ToastAction } from "@/components/ui/toast"

import { useState } from "react";

// Forms
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

// Fetching
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

const FormSchema = z.object({
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


export function SaveSettings(){

}
export function FetchSettings(){

}

export default function Home() {
  let devices = getDevices()
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      device_index: 0,
      saveSubtitles: true,
    },
  });

  function onSubmit(values: z.infer<typeof FormSchema>) {
    setIsDialogOpen(false); // Close the dialog
    toast({
        title: "Settings Saved",
        description: "Your settings have been successfully saved.",
        duration: 2000,
    });
    console.log('Saved settings:', values);
  }

  return (
    <main className="flex min-h-screen flex-col justify-between p-24">
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogTrigger asChild>
          <Button className="items-center sm:max-w-[150px]" onClick={() => setIsDialogOpen(true)}>
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
                          Save Transcription after recording.
                        </label>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <DialogFooter>
                <Button type="submit">Save changes</Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </main>
  );
}