"use client";
import { useRouter } from "next/navigation";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import React, { useState } from "react";
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
import { createPolicyVersion } from "@/lib/api";
import { useStackApp } from "@stackframe/stack";

const formSchema = z.object({
    tag: z.string({ description: "Name of the Version" }).min(1),
    repository: z.string({ description: "Repository" }).optional(),
    repository_version: z.string({ description: "Repository Version" }).min(0).optional(),
});

export function CreatePolicyVersionDialog({ policyId }: { policyId: string }) {
    const stackApp = useStackApp();
    const user = stackApp.getUser();
    const [open, setOpen] = useState(false);
    const router = useRouter();

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            tag: "",
            repository: "null",
            repository_version: "0",
        },
    });

    const onSubmit = async (data: any) => {
        await createPolicyVersion(user, { policy_id: policyId, ...data })
            .then(() => {
                setOpen(false);
                form.reset();
                toast("Policy Version Created", {
                    description: `Policy Version ${data.tag} has been created.`,
                    dismissible: true,
                });
                router.refresh();
            })
            .catch((error) => {
                console.error(error);
            });
    };

    const formFields: Array<React.ReactElement> = [];
    for (const fieldName in formSchema.shape) {
        const formField = formSchema.shape[fieldName];
        formFields.push(
            <FormField
                key={fieldName}
                name={fieldName as keyof typeof formSchema.shape}
                control={form.control}
                render={({ field }) => (
                    <FormItem>
                        <FormLabel htmlFor={fieldName}>{titleCase(fieldName)}</FormLabel>
                        <FormControl>
                            <Input placeholder={formField?.default} type="text" {...field} />
                        </FormControl>
                        <FormDescription>{formField?.description}</FormDescription>
                        <FormMessage>{form.formState.errors[fieldName]?.message}</FormMessage>
                    </FormItem>
                )}
            />,
        );
    }

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
                        {formFields}

                        <DialogFooter>
                            <Button type="submit">Create Policy</Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Form>
        </Dialog>
    );
}

function titleCase(str: string) {
    const spaced = str.replace(/_/g, " ");
    const words = spaced.split(" ");
    return words.map((word) => capitalize(word)).join(" ");
}

function capitalize(str: string) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
