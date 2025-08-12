"use client";

// React and Next.js
import { useState } from "react";
import { useRouter } from "next/navigation";

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
import { Sending } from "../../index";

const formSchema = z.object({
    name: z.string().min(1),
    description: z.string().min(0),
});

export interface CreatePolicyDialogConfig {
    projectId?: string;
    createPolicy: (data: { name: string; description: string }, projectId?: string) => Promise<any>;
    buttonText?: string;
    dialogTitle?: string;
}

export function CreatePolicyDialog({ config }: { config: CreatePolicyDialogConfig }) {
    const [open, setOpen] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const router = useRouter();

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            description: "",
        },
    });

    const onSubmit = async (data: z.infer<typeof formSchema>) => {
        setIsSubmitting(true);
        try {
            await config.createPolicy(data, config.projectId);
            setOpen(false);
            form.reset();
            toast("Policy Created", {
                description: `Policy ${data.name} has been created.`,
                dismissible: true,
            });
            router.refresh();
        } catch (error) {
            console.error(error);
            toast.error("Failed to create policy");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <Form {...form}>
                <DialogTrigger asChild>
                    <Button variant="outline">{config.buttonText || "Create Policy"}</Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>{config.dialogTitle || "Create a new Policy"}</DialogTitle>
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
                                        <Input placeholder="New Policy" type="text" {...field} />
                                    </FormControl>
                                    <FormDescription>Name of the new Policy</FormDescription>
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
                                        <Textarea placeholder="A brand new policy." {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        Description of the new Policy (optional)
                                    </FormDescription>
                                    <FormMessage>
                                        {form.formState.errors.description?.message}
                                    </FormMessage>
                                </FormItem>
                            )}
                        />
                        <DialogFooter>
                            <Button type="submit" disabled={isSubmitting}>
                                {isSubmitting ? <Sending /> : "Create Policy"}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Form>
        </Dialog>
    );
}