"use client";

import { useRouter } from "next/navigation";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useState, useEffect } from "react";
import { toast } from "sonner";

import { DataTable } from "@/components/data-table";
import { DetailsButton } from "@/components/details-button";
import { ShortenedID } from "@/components/shortened-id";
import { Button } from "@/components/ui/button";
import { parseDate } from "@/lib/utils";
import { ColumnDef } from "@tanstack/react-table";
import { DataSourceSpec } from "@vulkan-server/DataSourceSpec";
import { DataSource } from "@vulkan-server/DataSource";
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
import { createDataSource } from "@/lib/api";

export default function DataSourcesPage({ dataSources }: { dataSources: DataSource[] }) {
    const router = useRouter();
    const emptyMessage = "Create a data source to start using it in your workflows.";

    return (
        <div className="flex flex-col gap-4">
            <div className="flex gap-4">
                <Button variant="outline" onClick={() => router.refresh()}>
                    Refresh
                </Button>
                <CreateDataSourceDialog />
            </div>
            <DataTable
                columns={dataSourceTableColumns}
                data={dataSources}
                emptyMessage={emptyMessage}
                className="max-h-[67vh]"
            />
        </div>
    );
}

const formSchema = z.object({
    name: z.string().min(1),
    description: z.string().min(0),
    keys: z.string().transform((val) => val.split(',').map(s => s.trim()).filter(s => s !== '')),
    source: z.object({
        url: z.string().min(1),
        method: z.string().optional(),
        headers: z.string().optional().transform(val => {
            if (!val) return undefined;
            try {
                return JSON.parse(val);
            } catch (e) {
                return {};
            }
        }),
        params: z.string().optional().transform(val => {
            if (!val) return undefined;
            try {
                return JSON.parse(val);
            } catch (e) {
                return {};
            }
        }),
        body_schema: z.string().optional().transform(val => {
            if (!val) return undefined;
            try {
                return JSON.parse(val);
            } catch (e) {
                return {};
            }
        }),
        timeout: z.string().optional().transform(val => val ? parseInt(val) : undefined),
        retry: z.string().optional().transform(val => {
            if (!val) return undefined;
            try {
                return JSON.parse(val);
            } catch (e) {
                return undefined;
            }
        }),
        path: z.string().optional(),
        file_id: z.string().optional(),
    }),
    caching: z.object({
        enabled: z.boolean().optional(),
        ttl: z.string().optional().transform(val => val ? parseInt(val) : undefined)
    }).optional(),
    metadata: z.string().optional().transform((val) => {
        if (!val) return undefined;
        try {
            return JSON.parse(val);
        } catch (e) {
            return {};
        }
    })
});

function CreateDataSourceDialog() {
    const [open, setOpen] = useState(false);
    const [step, setStep] = useState(1);
    const router = useRouter();

    const headersParamsPlaceholderText = JSON.stringify({
        "Authorization": "Bearer {{secrets.API_TOKEN}}",
        "Content-Type": "application/json"
    }, null, 2);

    const retryPolicyPlaceholderText = JSON.stringify({
        max_retries: 3,
        initial_delay_ms: 1000,
        max_delay_ms: 10000,
        backoff_factor: 2
    }, null, 2);

    const bodySchemaPlaceholderText = JSON.stringify({
        "type": "object",
        "properties": {
            "query": { "type": "string" }
        }
    }, null, 2);

    const metadataPlaceholderText = JSON.stringify({ 
        owner: "team-name",
        environment: "production" 
    }, null, 2);

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            description: "",
            keys: "",
            source: {
                url: "",
                method: "GET",
                headers: "",
                params: "",
                body_schema: "",
                timeout: "",
                retry: "",
                path: "",
                file_id: "",
            },
            caching: {
                enabled: false,
                ttl: ""
            },
            metadata: ""
        },
        mode: "onChange"
    });

    useEffect(() => {
        if (!open) {
            setStep(1);
        }
    }, [open]);

    const goToNextStep = async () => {
        let fieldsToValidate: string[] = [];
        
        switch (step) {
            case 1:
                fieldsToValidate = ["name", "keys", "description"];
                break;
            case 2:
                fieldsToValidate = [
                    "source.url", "source.method", "source.headers", 
                    "source.params", "source.body_schema", "source.timeout",
                    "source.retry", "source.path", "source.file_id"
                ];
                break;
        }

        const result = await form.trigger(fieldsToValidate as any, { shouldFocus: true });
        if (result) {
            setStep(prevStep => prevStep + 1);
        }
    };

    const goToPreviousStep = () => {
        setStep(prevStep => Math.max(prevStep - 1, 1));
    };

    const onSubmit = async (data: any) => {
        // Only process submission on the final step
        if (step !== 3) {
            return;
        }
        
        const dataSourceSpec = {
            name: data.name,
            keys: data.keys,
            source: {
                url: data.source.url,
                method: data.source.method || undefined,
                headers: data.source.headers,
                params: data.source.params,
                body_schema: data.source.body_schema,
                timeout: data.source.timeout,
                retry: data.source.retry,
                path: data.source.path || "",
                file_id: data.source.file_id || "",
            },
            description: data.description || null,
            caching: data.caching?.enabled || data.caching?.ttl ? {
                enabled: data.caching.enabled,
                ttl: data.caching.ttl
            } : undefined,
            metadata: data.metadata || null
        };
        
        await createDataSource(dataSourceSpec)
            .then(() => {
                setOpen(false);
                form.reset();
                toast("Data Source Created", {
                    description: `Data Source ${data.name} has been created.`,
                    dismissible: true,
                });
                router.refresh();
            })
            .catch((error) => {
                console.error(error);
                toast("Error Creating Data Source", {
                    description: error.message || "An unknown error occurred",
                    dismissible: true,
                });
            });
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <Form {...form}>
                <DialogTrigger asChild>
                    <Button variant="outline">Create Data Source</Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Create a new Data Source - Step {step} of 3</DialogTitle>
                    </DialogHeader>
                    <form
                        className="flex flex-col gap-4 py-4"
                        onSubmit={(e) => {
                            // Only submit the form on the final step
                            if (step < 3) {
                                e.preventDefault();
                                return;
                            }
                            form.handleSubmit(onSubmit)(e);
                        }}
                    >
                        {step === 1 && (
                            <div className="space-y-4">
                                <FormField
                                    name="name"
                                    control={form.control}
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel htmlFor="name">Name *</FormLabel>
                                            <FormControl>
                                                <Input placeholder="New Data Source" type="text" {...field} />
                                            </FormControl>
                                            <FormDescription>Name of the new Data Source</FormDescription>
                                            <FormMessage>{form.formState.errors.name?.message}</FormMessage>
                                        </FormItem>
                                    )}
                                />
                                
                                <FormField
                                    name="keys"
                                    control={form.control}
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel htmlFor="keys">Keys *</FormLabel>
                                            <FormControl>
                                                <Input placeholder="key1, key2, key3" type="text" {...field} />
                                            </FormControl>
                                            <FormDescription>Comma-separated list of keys for this data source</FormDescription>
                                            <FormMessage>{form.formState.errors.keys?.message}</FormMessage>
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
                                                <Textarea placeholder="A brand new data source." {...field} />
                                            </FormControl>
                                            <FormDescription>
                                                Description of the new Data Source (optional)
                                            </FormDescription>
                                            <FormMessage>
                                                {form.formState.errors.description?.message}
                                            </FormMessage>
                                        </FormItem>
                                    )}
                                />
                            </div>
                        )}
                        
                        {step === 2 && (
                            <div className="space-y-4">
                                <h3 className="text-lg font-medium mb-4">Source Configuration</h3>
                                
                                <div className="grid grid-cols-2 gap-4">
                                    <FormField
                                        control={form.control}
                                        name="source.url"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>URL *</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="https://api.example.com/data" {...field} />
                                                </FormControl>
                                                <FormDescription>
                                                    Endpoint URL
                                                </FormDescription>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    
                                    <FormField
                                        control={form.control}
                                        name="source.method"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Method</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="GET" {...field} />
                                                </FormControl>
                                                <FormDescription>
                                                    HTTP method (GET, POST, etc.)
                                                </FormDescription>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>
                                
                                <div className="grid grid-cols-2 gap-4">
                                    <FormField
                                        control={form.control}
                                        name="source.timeout"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Timeout (ms)</FormLabel>
                                                <FormControl>
                                                    <Input type="number" min="0" placeholder="5000" {...field} />
                                                </FormControl>
                                                <FormDescription>
                                                    Request timeout in milliseconds
                                                </FormDescription>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    
                                    <FormField
                                        control={form.control}
                                        name="source.path"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Path</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="/data/path" {...field} />
                                                </FormControl>
                                                <FormDescription>
                                                    Path for file sources
                                                </FormDescription>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>
                                
                                <FormField
                                    control={form.control}
                                    name="source.file_id"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>File ID</FormLabel>
                                            <FormControl>
                                                <Input placeholder="file_123abc" {...field} />
                                            </FormControl>
                                            <FormDescription>
                                                ID for registered file sources
                                            </FormDescription>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                                
                                <FormField
                                    control={form.control}
                                    name="source.headers"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Headers</FormLabel>
                                            <FormControl>
                                                <Textarea
                                                    className="min-h-24 font-mono text-sm"
                                                    placeholder={headersParamsPlaceholderText}
                                                    {...field}
                                                />
                                            </FormControl>
                                            <FormDescription>
                                                HTTP headers in JSON format
                                            </FormDescription>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                                
                                <FormField
                                    control={form.control}
                                    name="source.params"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Query Parameters</FormLabel>
                                            <FormControl>
                                                <Textarea
                                                    className="min-h-24 font-mono text-sm"
                                                    placeholder={headersParamsPlaceholderText}
                                                    {...field}
                                                />
                                            </FormControl>
                                            <FormDescription>
                                                Query parameters in JSON format
                                            </FormDescription>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                                
                                <FormField
                                    control={form.control}
                                    name="source.body_schema"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Body Schema</FormLabel>
                                            <FormControl>
                                                <Textarea
                                                    className="min-h-24 font-mono text-sm"
                                                    placeholder={bodySchemaPlaceholderText}
                                                    {...field}
                                                />
                                            </FormControl>
                                            <FormDescription>
                                                JSON schema for request body
                                            </FormDescription>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                                
                                <FormField
                                    control={form.control}
                                    name="source.retry"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Retry Policy</FormLabel>
                                            <FormControl>
                                                <Textarea
                                                    className="min-h-24 font-mono text-sm"
                                                    placeholder={retryPolicyPlaceholderText}
                                                    {...field}
                                                />
                                            </FormControl>
                                            <FormDescription>
                                                Retry configuration in JSON format
                                            </FormDescription>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>
                        )}
                        
                        {step === 3 && (
                            <div className="space-y-4">
                                <div className="border p-4 rounded-md mb-4">
                                    <h3 className="text-lg font-medium mb-4">Caching Options</h3>
                                    
                                    <div className="grid grid-cols-2 gap-4">
                                        <FormField
                                            control={form.control}
                                            name="caching.enabled"
                                            render={({ field }) => (
                                                <FormItem className="flex flex-row items-center space-x-3 space-y-0">
                                                    <FormControl>
                                                        <input
                                                            type="checkbox"
                                                            className="h-4 w-4"
                                                            checked={field.value}
                                                            onChange={field.onChange}
                                                        />
                                                    </FormControl>
                                                    <div className="space-y-1 leading-none">
                                                        <FormLabel>Enable Caching</FormLabel>
                                                        <FormDescription>
                                                            Toggle caching for this data source
                                                        </FormDescription>
                                                    </div>
                                                </FormItem>
                                            )}
                                        />
                                        
                                        <FormField
                                            control={form.control}
                                            name="caching.ttl"
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>Cache TTL (seconds)</FormLabel>
                                                    <FormControl>
                                                        <Input type="number" min="0" placeholder="3600" {...field} />
                                                    </FormControl>
                                                    <FormDescription>
                                                        Time to live for cached data
                                                    </FormDescription>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                    </div>
                                </div>
                                
                                <FormField
                                    control={form.control}
                                    name="metadata"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Metadata</FormLabel>
                                            <FormControl>
                                                <Textarea
                                                    className="min-h-24 font-mono text-sm"
                                                    placeholder={metadataPlaceholderText}
                                                    {...field}
                                                />
                                            </FormControl>
                                            <FormDescription>
                                                Additional metadata in JSON format (optional)
                                            </FormDescription>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>
                        )}
                        
                        <div className="flex justify-between mt-4">
                            <Button 
                                type="button" 
                                variant="outline" 
                                onClick={goToPreviousStep}
                                disabled={step === 1}
                            >
                                Back
                            </Button>
                            
                            {step < 3 ? (
                                <Button 
                                    type="button" 
                                    onClick={(e) => {
                                        e.preventDefault();
                                        goToNextStep();
                                    }}
                                >
                                    Next
                                </Button>
                            ) : (
                                <Button type="submit">Create Data Source</Button>
                            )}
                        </div>
                    </form>
                </DialogContent>
            </Form>
        </Dialog>
    );
}

const dataSourceTableColumns: ColumnDef<DataSource>[] = [
    {
        accessorKey: "link",
        header: "",
        cell: ({ row }) => (
            <DetailsButton href={`/integrations/dataSources/${row.getValue("data_source_id")}`} />
        ),
    },
    {
        accessorKey: "data_source_id",
        header: "ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("data_source_id")} />,
    },
    {
        accessorKey: "name",
        header: "Name",
    },
    {
        accessorKey: "description",
        header: "Description",
        cell: ({ row }) => {
            const description: string = row.getValue("description");
            return description?.length > 0 ? description : "-";
        },
    },
    {
        accessorKey: "created_at",
        header: "Created At",
        cell: ({ row }) => parseDate(row.getValue("created_at")),
    },
    {
        accessorKey: "last_updated_at",
        header: "Last Updated At",
        cell: ({ row }) => parseDate(row.getValue("last_updated_at")),
    },
];
