"use client";

// React and Next.js
import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

// External libraries
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

// Vulkan packages
import {
    Button,
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
    Input,
    Textarea,
} from "@vulkanlabs/base/ui";
import { Sending } from "../animations";

const formSchema = z.object({
    name: z.string().min(1, "Name is required"),
    description: z.string().min(0),
    icon: z.string().min(0),
});

// Helper function to convert file to base64
const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            if (typeof reader.result === "string") {
                resolve(reader.result);
            } else {
                reject(new Error("Failed to convert file to base64"));
            }
        };
        reader.onerror = (error) => reject(error);
    });
};

export interface CreateComponentDialogConfig {
    createComponent: (data: { name: string; description: string; icon: string }) => Promise<any>;
    buttonText?: string;
    dialogTitle?: string;
}

export function CreateComponentDialog({ config }: { config: CreateComponentDialogConfig }) {
    const [open, setOpen] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const router = useRouter();

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            description: "",
            icon: "",
        },
    });

    const handleFileSelect = (file: File) => {
        if (file.type.startsWith("image/")) {
            setSelectedFile(file);
            fileToBase64(file)
                .then((base64) => {
                    form.setValue("icon", base64);
                })
                .catch((error) => {
                    console.error("Error converting file to base64:", error);
                    toast.error("Failed to process image file");
                });
        } else {
            toast.error("Please select an image file");
        }
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    };

    const onSubmit = async (data: z.infer<typeof formSchema>) => {
        setIsSubmitting(true);
        try {
            await config.createComponent(data);
            setOpen(false);
            form.reset();
            setSelectedFile(null);
            toast("Component Created", {
                description: `Component ${data.name} has been created.`,
                dismissible: true,
            });
            router.refresh();
        } catch (error) {
            console.error(error);
            toast.error("Failed to create component");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <Form {...form}>
                <DialogTrigger asChild>
                    <Button variant="outline">{config.buttonText || "Create Component"}</Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>{config.dialogTitle || "Create a new Component"}</DialogTitle>
                    </DialogHeader>
                    <form
                        className="flex flex-col gap-4 py-4"
                        onSubmit={form.handleSubmit(onSubmit)}
                    >
                        <FormField
                            name="name"
                            control={form.control}
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel htmlFor="name">Name</FormLabel>
                                    <FormControl>
                                        <Input placeholder="New Component" type="text" {...field} />
                                    </FormControl>
                                    <FormDescription>Name of the new Component</FormDescription>
                                    <FormMessage>{form.formState.errors.name?.message}</FormMessage>
                                </FormItem>
                            )}
                        />
                        <FormField
                            name="description"
                            control={form.control}
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel htmlFor="description">Description</FormLabel>
                                    <FormControl>
                                        <Textarea placeholder="A brand new component." {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        Description of the new Component (optional)
                                    </FormDescription>
                                    <FormMessage>
                                        {form.formState.errors.description?.message}
                                    </FormMessage>
                                </FormItem>
                            )}
                        />
                        <FormField
                            name="icon"
                            control={form.control}
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel htmlFor="icon">Icon</FormLabel>
                                    <FormControl>
                                        <div
                                            className={`border-2 border-dashed rounded-lg p-4 text-center 
                                                transition-colors ${
                                                    dragActive
                                                        ? "border-primary bg-primary/10"
                                                        : "border-gray-300 hover:border-gray-400"
                                                }`}
                                            onDragEnter={handleDrag}
                                            onDragLeave={handleDrag}
                                            onDragOver={handleDrag}
                                            onDrop={handleDrop}
                                        >
                                            <input
                                                type="file"
                                                accept="image/*"
                                                className="hidden"
                                                id="icon-upload"
                                                onChange={(e) => {
                                                    const file = e.target.files?.[0];
                                                    if (file) {
                                                        handleFileSelect(file);
                                                    }
                                                }}
                                            />
                                            <label htmlFor="icon-upload" className="cursor-pointer">
                                                {selectedFile ? (
                                                    <div className="space-y-2">
                                                        <Image
                                                            src={field.value}
                                                            alt="Selected icon"
                                                            width={64}
                                                            height={64}
                                                            className="mx-auto h-16 w-16 object-contain rounded"
                                                        />
                                                        <p className="text-sm text-gray-600">
                                                            {selectedFile.name}
                                                        </p>
                                                        <Button
                                                            type="button"
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={() => {
                                                                setSelectedFile(null);
                                                                form.setValue("icon", "");
                                                            }}
                                                        >
                                                            Remove
                                                        </Button>
                                                    </div>
                                                ) : (
                                                    <div className="space-y-2">
                                                        <div className="text-4xl">📁</div>
                                                        <p className="text-sm text-gray-600">
                                                            Drag and drop an image here, or click to
                                                            select
                                                        </p>
                                                        <p className="text-xs text-gray-500">
                                                            Supports: JPG, PNG, GIF, SVG
                                                        </p>
                                                    </div>
                                                )}
                                            </label>
                                        </div>
                                    </FormControl>
                                    <FormDescription>
                                        Upload an image for the component icon
                                    </FormDescription>
                                    <FormMessage>{form.formState.errors.icon?.message}</FormMessage>
                                </FormItem>
                            )}
                        />
                        <DialogFooter>
                            <Button type="submit" disabled={isSubmitting}>
                                {isSubmitting ? <Sending /> : "Create Component"}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Form>
        </Dialog>
    );
}
