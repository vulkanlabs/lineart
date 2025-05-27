"use client";

import { useRouter } from "next/navigation";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
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
import { Switch } from "@/components/ui/switch";
import { createDataSourceAction } from "./actions";

const formSchema = z.object({
    name: z
        .string()
        .min(1)
        .regex(/^[a-zA-Z0-9-_]+$/, {
            message: "Name must only contain letters, numbers, dashes, and underscores",
        }),
    description: z.string().min(0),
    keys: z
        .string()
        .optional()
        .transform((val) =>
            val
                .split(",")
                .map((s) => s.trim())
                .filter((s) => s !== ""),
        ),
    source: z.object({
        url: z.string().min(1),
        method: z.string().optional(),
        headers: z.string().optional().transform(parseJSON),
        params: z.string().optional().transform(parseJSON),
        body_schema: z.string().optional().transform(parseJSON),
        timeout: z
            .string()
            .optional()
            .transform((val) => (val ? parseInt(val) : undefined)),
        retry: z
            .string()
            .optional()
            .transform((val) => {
                if (!val) return undefined;
                try {
                    return JSON.parse(val);
                } catch (e) {
                    return undefined;
                }
            }),
    }),
    caching: z
        .object({
            enabled: z.boolean().optional(),
            ttl: z
                .string()
                .optional()
                .transform((val) => (val ? parseInt(val) : undefined)),
        })
        .optional(),
    metadata: z.string().optional().transform(parseJSON),
});

function parseJSON(val: string) {
    {
        if (!val) return undefined;
        try {
            return JSON.parse(val);
        } catch (e) {
            return {};
        }
    }
}

export function CreateDataSourceDialog() {
    const [open, setOpen] = useState(false);
    const [step, setStep] = useState(1);
    const router = useRouter();

    const metadataPlaceholderText = JSON.stringify(
        {
            owner: "team-name",
            environment: "production",
        },
        null,
        2,
    );

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            description: "",
            keys: [],
            source: {
                url: "",
                method: "GET",
                headers: "",
                params: "",
                body_schema: "",
                timeout: 0,
                retry: "",
            },
            caching: {
                enabled: false,
                ttl: 0,
            },
            metadata: "",
        },
        mode: "onChange",
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
                    "source.url",
                    "source.method",
                    "source.headers",
                    "source.params",
                    "source.body_schema",
                    "source.timeout",
                    "source.retry",
                ];
                break;
        }

        const isValid = await form.trigger(fieldsToValidate as any, { shouldFocus: true });
        if (isValid) {
            setStep((prevStep) => prevStep + 1);
        }
    };

    const goToPreviousStep = () => {
        setStep((prevStep) => Math.max(prevStep - 1, 1));
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
                method: data.source.method,
                headers: data.source.headers,
                params: data.source.params,
                body_schema: data.source.body_schema,
                timeout: data.source.timeout,
                retry: data.source.retry,
                // ignore these fields for now
                path: "",
                file_id: "",
            },
            description: data.description || null,
            caching:
                data.caching?.enabled || data.caching?.ttl
                    ? {
                          enabled: data.caching.enabled,
                          ttl: data.caching.ttl,
                      }
                    : undefined,
            metadata: data.metadata || null,
        };

        await createDataSourceAction(dataSourceSpec)
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
                        onSubmit={(e) => form.handleSubmit(onSubmit)(e)}
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
                                                <Input placeholder="" type="text" {...field} />
                                            </FormControl>
                                            <FormDescription>
                                                Name of the new Data Source
                                            </FormDescription>
                                            <FormMessage>
                                                {form.formState.errors.name?.message}
                                            </FormMessage>
                                        </FormItem>
                                    )}
                                />

                                <FormField
                                    name="keys"
                                    control={form.control}
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel htmlFor="keys">Keys</FormLabel>
                                            <FormControl>
                                                <Input
                                                    placeholder="key1, key2, key3"
                                                    type="text"
                                                    {...field}
                                                />
                                            </FormControl>
                                            <FormDescription>
                                                Comma-separated list of keys for this Data Source
                                            </FormDescription>
                                            <FormMessage>
                                                {form.formState.errors.keys?.message}
                                            </FormMessage>
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
                                                <Textarea
                                                    placeholder="A brand new data source."
                                                    {...field}
                                                />
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
                                <HTTPOptions form={form} />
                            </div>
                        )}

                        {step === 3 && (
                            <div className="space-y-4">
                                <CachingOptions form={form} />

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

function HTTPOptions({ form }) {
    const headersParamsPlaceholderText = JSON.stringify(
        {
            Authorization: "Bearer {{secrets.API_TOKEN}}",
            "Content-Type": "application/json",
        },
        null,
        2,
    );

    const queryParamsPlaceholderText = JSON.stringify(
        {
            key1: "value1",
            key2: "value2",
        },
        null,
        2,
    );

    const retryPolicyPlaceholderText = JSON.stringify(
        {
            max_retries: 3,
            backoff_factor: 2,
            status_forcelist: [500, 502, 503, 504],
        },
        null,
        2,
    );

    const bodySchemaPlaceholderText = JSON.stringify(
        {
            type: "object",
            properties: {
                query: { type: "string" },
            },
        },
        null,
        2,
    );

    return (
        <>
            <FormField
                control={form.control}
                name="source.url"
                render={({ field }) => (
                    <FormItem>
                        <FormLabel>URL *</FormLabel>
                        <FormControl>
                            <Input placeholder="https://api.example.com/data" {...field} />
                        </FormControl>
                        <FormDescription>Endpoint URL</FormDescription>
                        <FormMessage />
                    </FormItem>
                )}
            />

            <div className="grid grid-cols-2 gap-4">
                <FormField
                    control={form.control}
                    name="source.method"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Method</FormLabel>
                            <FormControl>
                                <Input placeholder="GET" {...field} />
                            </FormControl>
                            <FormDescription>HTTP method (GET, POST, etc.)</FormDescription>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                <FormField
                    control={form.control}
                    name="source.timeout"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Timeout (ms)</FormLabel>
                            <FormControl>
                                <Input type="number" min="0" placeholder="5000" {...field} />
                            </FormControl>
                            <FormDescription>Request timeout in milliseconds</FormDescription>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            </div>

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
                        <FormDescription>HTTP headers in JSON format</FormDescription>
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
                                placeholder={queryParamsPlaceholderText}
                                {...field}
                            />
                        </FormControl>
                        <FormDescription>Query parameters in JSON format</FormDescription>
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
                        <FormDescription>JSON schema for request body</FormDescription>
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
                        <FormDescription>Retry configuration in JSON format</FormDescription>
                        <FormMessage />
                    </FormItem>
                )}
            />
        </>
    );
}

function CachingOptions({ form }) {
    const [days, setDays] = useState(0);
    const [hours, setHours] = useState(0);
    const [minutes, setMinutes] = useState(0);
    const [seconds, setSeconds] = useState(0);
    const isCachingEnabled = form.watch("caching.enabled");

    // Initialize time fields from seconds when the component loads or ttl value changes
    useEffect(() => {
        const totalSeconds = form.watch("caching.ttl") ? parseInt(form.watch("caching.ttl")) : 0;
        if (totalSeconds > 0) {
            const d = Math.floor(totalSeconds / 86400);
            const h = Math.floor((totalSeconds % 86400) / 3600);
            const m = Math.floor((totalSeconds % 3600) / 60);
            const s = totalSeconds % 60;

            setDays(d);
            setHours(h);
            setMinutes(m);
            setSeconds(s);
        }
    }, [form.watch("caching.ttl")]);

    // Calculate total seconds when any time unit changes
    const calculateTotalSeconds = useCallback(() => {
        const d = parseInt(days.toString()) || 0;
        const h = parseInt(hours.toString()) || 0;
        const m = parseInt(minutes.toString()) || 0;
        const s = parseInt(seconds.toString()) || 0;

        return d * 86400 + h * 3600 + m * 60 + s;
    }, [days, hours, minutes, seconds]);

    // Update form value when any time unit changes
    useEffect(() => {
        const totalSeconds = calculateTotalSeconds();
        form.setValue("caching.ttl", totalSeconds.toString());
    }, [days, hours, minutes, seconds, calculateTotalSeconds, form]);

    return (
        <div className="border p-4 rounded-md mb-4">
            <h3 className="text-lg font-medium mb-4">Caching Options</h3>

            <div className="mb-6">
                <FormField
                    control={form.control}
                    name="caching.enabled"
                    render={({ field }) => (
                        <FormItem className="flex flex-row items-center justify-between space-y-0">
                            <div className="space-y-0.5">
                                <FormLabel className="text-base">Enable Caching</FormLabel>
                                <FormDescription>
                                    Toggle caching for this data source
                                </FormDescription>
                            </div>
                            <FormControl>
                                <Switch checked={field.value} onCheckedChange={field.onChange} />
                            </FormControl>
                        </FormItem>
                    )}
                />
            </div>

            {isCachingEnabled && (
                <FormField
                    control={form.control}
                    name="caching.ttl"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Cache TTL</FormLabel>
                            <div className="grid grid-cols-4 gap-2">
                                <div>
                                    <Input
                                        type="number"
                                        min="0"
                                        placeholder="0"
                                        value={days}
                                        onChange={(e) => setDays(parseInt(e.target.value) || 0)}
                                    />
                                    <span className="text-xs text-gray-500">Days</span>
                                </div>
                                <div>
                                    <Input
                                        type="number"
                                        min="0"
                                        max="23"
                                        placeholder="0"
                                        value={hours}
                                        onChange={(e) => setHours(parseInt(e.target.value) || 0)}
                                    />
                                    <span className="text-xs text-gray-500">Hours</span>
                                </div>
                                <div>
                                    <Input
                                        type="number"
                                        min="0"
                                        max="59"
                                        placeholder="0"
                                        value={minutes}
                                        onChange={(e) => setMinutes(parseInt(e.target.value) || 0)}
                                    />
                                    <span className="text-xs text-gray-500">Minutes</span>
                                </div>
                                <div>
                                    <Input
                                        type="number"
                                        min="0"
                                        max="59"
                                        placeholder="0"
                                        value={seconds}
                                        onChange={(e) => setSeconds(parseInt(e.target.value) || 0)}
                                    />
                                    <span className="text-xs text-gray-500">Seconds</span>
                                </div>
                            </div>
                            <FormDescription>
                                Time to live for cached data (total: {calculateTotalSeconds()}{" "}
                                seconds)
                            </FormDescription>
                            <FormMessage />
                            <input type="hidden" {...field} />
                        </FormItem>
                    )}
                />
            )}
        </div>
    );
}
