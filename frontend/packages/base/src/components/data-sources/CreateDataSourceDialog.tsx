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
import type { DataSourceSpec, DataSource } from "@vulkanlabs/client-open";
import {
    Button,
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    Input,
    Form,
    FormField,
    FormControl,
    FormDescription,
    FormItem,
    FormLabel,
    FormMessage,
} from "../ui";
import { Sending } from "../animations";

const formSchema = z.object({
    name: z.string().min(1, "Name is required"),
    description: z.string().optional(),
});

export interface CreateDataSourceDialogConfig {
    createDataSource: (spec: DataSourceSpec, projectId?: string) => Promise<DataSource>;
    projectId?: string;
    buttonText?: string;
    dialogTitle?: string;
}

/**
 * Data source creation dialog component
 * @param {Object} props - Component properties
 * @param {CreateDataSourceDialogConfig} props.config - Dialog configuration
 * @returns {JSX.Element} Modal dialog with data source creation form
 */
export function CreateDataSourceDialog({ config }: { config: CreateDataSourceDialogConfig }) {
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
            // Create data source with minimal spec
            const dataSourceSpec: DataSourceSpec = {
                name: data.name,
                source: {
                    url: "",
                    method: "GET",
                    response_type: "JSON",
                    headers: {},
                    params: {},
                    body: {},
                    timeout: 5000,
                    retry: {
                        max_retries: 3,
                        backoff_factor: 2,
                        status_forcelist: [500, 502, 503, 504],
                    },
                    path: "",
                    file_id: "",
                },
                description: data.description || null,
                caching: {
                    enabled: false,
                    ttl: {
                        seconds: 0,
                    },
                },
                metadata: {},
            };

            const createdDataSource = await config.createDataSource(
                dataSourceSpec,
                config.projectId,
            );
            setOpen(false);
            form.reset();
            toast("Data Source Created", {
                description: `Data Source ${data.name} has been created.`,
                dismissible: true,
                action: {
                    label: "Configure Now →",
                    onClick: () => router.push(`/data-sources/${createdDataSource.data_source_id}`),
                },
            });
            router.refresh();
        } catch (error) {
            console.error(error);
            toast.error("Failed to create data source");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <Form {...form}>
                <DialogTrigger asChild>
                    <Button variant="outline">{config.buttonText || "Create Data Source"}</Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>
                            {config.dialogTitle || "Create a new Data Source"}
                        </DialogTitle>
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
                                        <Input
                                            placeholder="New Data Source"
                                            type="text"
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormDescription>Name of the new Data Source</FormDescription>
                                    <FormMessage>{form.formState.errors.name?.message}</FormMessage>
                                </FormItem>
                            )}
                        />
                        <FormField
                            name="description"
                            control={form.control}
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel htmlFor="description">
                                        Description (Optional)
                                    </FormLabel>
                                    <FormControl>
                                        <Input
                                            placeholder="A brief description of this data source"
                                            type="text"
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormDescription>
                                        Brief description of the data source
                                    </FormDescription>
                                    <FormMessage>
                                        {form.formState.errors.description?.message}
                                    </FormMessage>
                                </FormItem>
                            )}
                        />
                        <DialogFooter>
                            <Button type="submit" disabled={isSubmitting}>
                                {isSubmitting ? <Sending /> : "Create Data Source"}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Form>
        </Dialog>
    );
}
