"use client";

import { useRouter } from "next/navigation";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useState } from "react";
import { toast } from "sonner";

import { DataTable } from "@/components/data-table";
import { DetailsButton } from "@/components/details-button";
import { ShortenedID } from "@/components/shortened-id";
import { Button } from "@/components/ui/button";
import { parseDate } from "@/lib/utils";
import { ColumnDef } from "@tanstack/react-table";
import { Policy } from "@vulkan-server/Policy";
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
import { useStackApp } from "@stackframe/stack";

export function PoliciesPage({ policies }: { policies: any[] }) {
    const router = useRouter();

    return (
        <div>
            <div className="flex gap-4">
                <Button variant="outline" onClick={() => router.refresh()}>
                    Refresh
                </Button>
                <CreatePolicyDialog />
            </div>
            <div className="my-4">
                <DataTable
                    columns={PolicyTableColumns}
                    data={policies}
                    emptyMessage="You don't have any policies yet."
                    className="max-h-[66vh]"
                />
            </div>
        </div>
    );
}

const formSchema = z.object({
    name: z.string().min(1),
    description: z.string().min(0),
});

function CreatePolicyDialog() {
    const stackApp = useStackApp();
    const user = stackApp.getUser();
    const [open, setOpen] = useState(false);
    const router = useRouter();

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            description: "",
        },
    });

    const onSubmit = async (data: any) => {
        await createPolicy(user, data)
            .then(() => {
                setOpen(false);
                form.reset();
                toast("Policy Created", {
                    description: `Policy ${data.name} has been created.`,
                    dismissible: true,
                });
                router.refresh();
            })
            .catch((error) => {
                console.error(error);
            });
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
                            <Button type="submit">Create Policy</Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Form>
        </Dialog>
    );
}

const PolicyTableColumns: ColumnDef<Policy>[] = [
    {
        accessorKey: "link",
        header: "",
        cell: ({ row }) => (
            <DetailsButton href={`/policies/${row.getValue("policy_id")}/overview`} />
        ),
    },
    {
        header: "ID",
        accessorKey: "policy_id",
        cell: ({ row }) => <ShortenedID id={row.getValue("policy_id")} />,
    },
    { header: "Name", accessorKey: "name" },
    {
        header: "Description",
        accessorKey: "description",
        cell: ({ row }) => row.getValue("description") || "-",
    },
    {
        header: "Active Version",
        accessorKey: "active_policy_version_id",
        cell: ({ row }) =>
            row.getValue("active_policy_version_id") == null ? (
                "-"
            ) : (
                <ShortenedID id={row.getValue("active_policy_version_id")} />
            ),
    },
    {
        header: "Last Updated At",
        accessorKey: "last_updated_at",
        cell: ({ row }) => parseDate(row.getValue("last_updated_at")),
    },
];
