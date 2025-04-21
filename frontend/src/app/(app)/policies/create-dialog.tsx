"use client";

import { useRouter } from "next/navigation";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
    Form,
    FormField,
    FormControl,
    FormDescription,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { createPolicy } from "@/lib/api";
import { Sending } from "@/components/animations/sending";

const formSchema = z.object({
    name: z.string().min(1),
    description: z.string().min(0),
});

export function CreatePolicyDialog() {
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

    const onSubmit = async (data: any) => {
        setIsSubmitting(true);
        try {
            await createPolicy( data);
            setOpen(false);
            form.reset();
            toast("Policy Created", {
                description: `Policy ${data.name} has been created.`,
                dismissible: true,
            });
            router.refresh();
        } catch (error) {
            console.error(error);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <Form {...form}>
                <DialogTrigger asChild>
                    <Button variant="outline">Create Policy</Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>Create a new Policy</DialogTitle>
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
