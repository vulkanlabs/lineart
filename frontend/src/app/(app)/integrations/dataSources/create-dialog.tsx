"use client";

import { useRouter } from "next/navigation";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { ChevronDown, ChevronRight } from "lucide-react";

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
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
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
    source: z.object({
        url: z
            .string()
            .min(1, "URL is required")
            .url("Please enter a valid URL")
            .regex(/^https?:\/\//, {
                message: "URL must start with http:// or https://",
            }),
        method: z.string().optional(),
        headers: z.string().optional().transform(parseJSON),
        params: z.string().optional().transform(parseJSON),
        body: z.string().optional().transform(parseJSON),
        timeout: z.number().optional(),
        retry: z
            .object({
                max_retries: z.number().optional(),
                backoff_factor: z.number().optional(),
                status_forcelist: z.array(z.number()).optional(),
            })
            .optional(),
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
            source: {
                url: "",
                method: "GET",
                headers: "",
                params: "",
                body: "",
                timeout: 5000,
                retry: {
                    max_retries: 3,
                    backoff_factor: 2,
                    status_forcelist: [500, 502, 503, 504],
                },
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
                fieldsToValidate = ["name", "description", "metadata"];
                break;
            case 2:
                fieldsToValidate = [
                    "source.url",
                    "source.method",
                    "source.headers",
                    "source.params",
                    "source.body",
                    "source.timeout",
                    "source.retry.max_retries",
                    "source.retry.backoff_factor",
                    "source.retry.status_forcelist",
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
            source: {
                url: data.source.url,
                method: data.source.method,
                headers: data.source.headers,
                params: data.source.params,
                body: data.source.body,
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
                                <h3 className="text-lg font-medium mb-4">Basic Options</h3>
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

                        {step === 2 && (
                            <div className="space-y-4">
                                <h3 className="text-lg font-medium mb-4">HTTP Options</h3>
                                <HTTPOptions form={form} />
                            </div>
                        )}

                        {step === 3 && (
                            <div className="space-y-4">
                                <h3 className="text-lg font-medium mb-4">Caching Options</h3>
                                <CachingOptions form={form} />
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
    const [showRetryPolicy, setShowRetryPolicy] = useState(false);
    const headersParamsPlaceholderText = JSON.stringify(
        {
            // Authorization: "Bearer {{secrets.API_TOKEN}}",
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

    const bodyPlaceholderText = JSON.stringify(
        {
            key1: "value1",
            key2: "value2",
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
                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select HTTP method" />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    <SelectItem value="GET">GET</SelectItem>
                                    <SelectItem value="POST">POST</SelectItem>
                                    <SelectItem value="PUT">PUT</SelectItem>
                                    <SelectItem value="PATCH">PATCH</SelectItem>
                                    <SelectItem value="DELETE">DELETE</SelectItem>
                                    <SelectItem value="HEAD">HEAD</SelectItem>
                                    <SelectItem value="OPTIONS">OPTIONS</SelectItem>
                                </SelectContent>
                            </Select>
                            <FormDescription>HTTP method for the request</FormDescription>
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
                name="source.body"
                render={({ field }) => (
                    <FormItem>
                        <FormLabel>Body</FormLabel>
                        <FormControl>
                            <Textarea
                                className="min-h-24 font-mono text-sm"
                                placeholder={bodyPlaceholderText}
                                {...field}
                            />
                        </FormControl>
                        <FormDescription>HTTP body in JSON format</FormDescription>
                        <FormMessage />
                    </FormItem>
                )}
            />

            <div className="space-y-4">
                <div
                    className="flex items-center gap-2 cursor-pointer"
                    onClick={() => setShowRetryPolicy(!showRetryPolicy)}
                >
                    <FormLabel className="cursor-pointer">Retry Policy</FormLabel>
                    {showRetryPolicy ? (
                        <ChevronDown className="h-4 w-4" />
                    ) : (
                        <ChevronRight className="h-4 w-4" />
                    )}
                </div>

                {showRetryPolicy && (
                    <div className="border rounded-md p-4">
                        <div className="grid grid-cols-1 gap-4">
                            <FormField
                                control={form.control}
                                name="source.retry.max_retries"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Max Retries</FormLabel>
                                        <FormControl>
                                            <Input
                                                type="number"
                                                min="0"
                                                placeholder="3"
                                                {...field}
                                                onChange={(e) =>
                                                    field.onChange(parseInt(e.target.value) || 0)
                                                }
                                            />
                                        </FormControl>
                                        <FormDescription>
                                            Maximum number of retry attempts
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="source.retry.backoff_factor"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Backoff Factor</FormLabel>
                                        <FormControl>
                                            <Input
                                                type="number"
                                                min="0"
                                                step="0.1"
                                                placeholder="2"
                                                {...field}
                                                onChange={(e) =>
                                                    field.onChange(parseFloat(e.target.value) || 0)
                                                }
                                            />
                                        </FormControl>
                                        <FormDescription>
                                            Exponential backoff multiplier
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="source.retry.status_forcelist"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Status Force List</FormLabel>
                                        <FormControl>
                                            <Input
                                                placeholder="500,502,503,504"
                                                {...field}
                                                value={field.value ? field.value.join(",") : ""}
                                                onChange={(e) => {
                                                    const values = e.target.value
                                                        .split(",")
                                                        .map((v) => parseInt(v.trim()))
                                                        .filter((v) => !isNaN(v));
                                                    field.onChange(values);
                                                }}
                                            />
                                        </FormControl>
                                        <FormDescription>
                                            HTTP status codes to retry (comma-separated)
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>
                    </div>
                )}
            </div>
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
        <>
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
        </>
    );
}
