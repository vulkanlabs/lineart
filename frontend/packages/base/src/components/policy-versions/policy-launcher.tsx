"use client";

// React and Next.js
import { useState, useEffect } from "react";
import Link from "next/link";

// External libraries
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, UseFormReturn } from "react-hook-form";
import {
    Play,
    Settings,
    CheckCircle,
    AlertCircle,
    Link as LinkIcon,
    Terminal,
} from "lucide-react";

// Vulkan packages
import { RunCreated } from "@vulkanlabs/client-open";

// Local components
import {
    Button,
    Dialog,
    DialogContent,
    DialogTitle,
    DialogTrigger,
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
    Textarea,
} from "../../ui";
import { Sending } from "../animations";

export interface PolicyLauncherConfig {
    policyVersionId: string;
    inputSchema: Record<string, string>;
    configVariables?: string[];
    createRunByPolicyVersion: (params: {
        policyVersionId: string;
        bodyCreateRunByPolicyVersion: {
            input_data: any;
            config_variables: any;
        };
        projectId?: string;
    }) => Promise<RunCreated>;
    projectId?: string;
}

export interface PolicyLauncherPageConfig extends PolicyLauncherConfig {}

export interface PolicyLauncherButtonConfig extends PolicyLauncherConfig {}

export function PolicyLauncherPage({ config }: { config: PolicyLauncherPageConfig }) {
    const { policyVersionId, inputSchema, configVariables } = config;
    const [createdRun, setCreatedRun] = useState<RunCreated | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const [copiedUrl, setCopiedUrl] = useState(false);
    const [copiedCurl, setCopiedCurl] = useState(false);
    const [currentFormData, setCurrentFormData] = useState<{
        input_data: string;
        config_variables: string;
    }>({
        input_data: JSON.stringify(asInputData(inputSchema), null, 2),
        config_variables: JSON.stringify(asConfigMap(configVariables || []), null, 2),
    });

    const getApiUrl = () => {
        const baseUrl =
            process.env.NEXT_PUBLIC_VULKAN_SERVER_URL ||
            (typeof window !== "undefined" ? window.location.origin : "");
        return `${baseUrl}/policy-versions/${policyVersionId}/runs`;
    };

    const handleCopyUrl = async () => {
        try {
            const url = getApiUrl();
            await navigator.clipboard.writeText(url);
            setCopiedUrl(true);
            setTimeout(() => setCopiedUrl(false), 2000);
        } catch (err) {
            console.error("Failed to copy URL:", err);
        }
    };

    const handleCopyCurl = async () => {
        try {
            const url = getApiUrl();
            const curlCommand = `curl -X POST "${url}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "input_data": ${currentFormData.input_data},
    "config_variables": ${currentFormData.config_variables}
  }'`;

            await navigator.clipboard.writeText(curlCommand);
            setCopiedCurl(true);
            setTimeout(() => setCopiedCurl(false), 2000);
        } catch (err) {
            console.error("Failed to copy curl command:", err);
        }
    };

    return (
        <div className="flex flex-col p-8 gap-8">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold tracking-tight">Launcher</h1>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleCopyUrl}>
                        <LinkIcon className="h-4 w-4 mr-2" />
                        {copiedUrl ? "Copied!" : "Copy URL"}
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleCopyCurl}>
                        <Terminal className="h-4 w-4 mr-2" />
                        {copiedCurl ? "Copied!" : "Copy curl"}
                    </Button>
                </div>
            </div>
            <div>
                <LaunchRunForm
                    config={config}
                    setCreatedRun={setCreatedRun}
                    setError={setError}
                    defaultInputData={asInputData(inputSchema)}
                    defaultConfigVariables={asConfigMap(configVariables || [])}
                    onFormDataChange={setCurrentFormData}
                />
            </div>
            {createdRun && (
                <RunCreatedCard createdRun={createdRun} closeDialog={() => setCreatedRun(null)} />
            )}
            {error && <RunCreationErrorCard error={error} onRetry={() => setError(null)} />}
        </div>
    );
}

export function PolicyLauncherButton({ config }: { config: PolicyLauncherButtonConfig }) {
    const { inputSchema, configVariables } = config;
    const [createdRun, setCreatedRun] = useState<RunCreated | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const [open, setOpen] = useState(false);

    const handleOpenChange = (open: boolean) => {
        setOpen(open);
        if (!open) {
            setError(null);
            setCreatedRun(null);
        }
    };

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogTrigger asChild>
                <Button
                    variant="outline"
                    size="sm"
                    className={
                        "px-2 py-1 text-xs h-auto " +
                        "border-input bg-background hover:bg-accent hover:text-accent-foreground " +
                        "transition-all duration-200 shadow-sm hover:shadow-md"
                    }
                    title="Launch a new policy run"
                >
                    <Play className="h-3 w-3 mr-1" />
                    <span>Launch Run</span>
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl w-[90vw] max-h-[85vh] overflow-y-auto">
                <div className="flex items-center justify-between pb-4 border-b">
                    <div className="space-y-1">
                        <DialogTitle className="text-xl font-semibold leading-none tracking-tight">
                            {createdRun
                                ? "Run Launched Successfully"
                                : error
                                  ? "Launch Failed"
                                  : "Launch a New Run"}
                        </DialogTitle>
                        <p className="text-sm text-muted-foreground">
                            {createdRun
                                ? "Your policy run has been created and is now executing."
                                : error
                                  ? "There was an error launching your run."
                                  : "Configure parameters and launch a run for this policy version."}
                        </p>
                    </div>
                </div>

                <div className="mt-6">
                    {!error && !createdRun && (
                        <LaunchRunForm
                            config={config}
                            defaultConfigVariables={asConfigMap(configVariables || [])}
                            defaultInputData={asInputData(inputSchema)}
                            setCreatedRun={setCreatedRun}
                            setError={setError}
                        />
                    )}
                    {error && (
                        <RunCreationErrorCard
                            error={error}
                            onRetry={() => {
                                setError(null);
                            }}
                        />
                    )}
                    {createdRun && (
                        <RunCreatedCard
                            createdRun={createdRun}
                            closeDialog={() => handleOpenChange(false)}
                        />
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}

const formSchema = z.object({
    input_data: z.string().refine(ensureJSON, { message: "Not a valid JSON object" }),
    config_variables: z
        .string()
        .nullable()
        .refine(ensureJSON, { message: "Not a valid JSON object" }),
});

type LaunchRunFormProps = {
    config: PolicyLauncherConfig;
    defaultInputData: Object;
    defaultConfigVariables: Object;
    setCreatedRun: (run: RunCreated | null) => void;
    setError: (error: Error | null) => void;
    onFormDataChange?: (data: { input_data: string; config_variables: string }) => void;
};

function LaunchRunForm({
    config,
    defaultInputData,
    defaultConfigVariables,
    setCreatedRun,
    setError,
    onFormDataChange,
}: LaunchRunFormProps) {
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            input_data: JSON.stringify(defaultInputData, null, 4),
            config_variables: JSON.stringify(defaultConfigVariables, null, 4),
        },
    });

    // Watch form changes and update parent component
    const watchedValues = form.watch();

    useEffect(() => {
        if (onFormDataChange) {
            onFormDataChange({
                input_data: watchedValues.input_data || JSON.stringify(defaultInputData, null, 2),
                config_variables:
                    watchedValues.config_variables ||
                    JSON.stringify(defaultConfigVariables, null, 2),
            });
        }
    }, [
        watchedValues.input_data,
        watchedValues.config_variables,
        onFormDataChange,
        defaultInputData,
        defaultConfigVariables,
    ]);

    const setDefaults = () => {
        form.setValue("input_data", JSON.stringify(defaultInputData, null, 4));
        form.setValue("config_variables", JSON.stringify(defaultConfigVariables, null, 4));
    };

    const [submitting, setSubmitting] = useState(false);

    async function onSubmit(values: z.infer<typeof formSchema>) {
        const body = {
            input_data: JSON.parse(values.input_data),
            config_variables: JSON.parse(values.config_variables || "{}"),
        };

        setSubmitting(true);
        setError(null);
        setCreatedRun(null);
        config
            .createRunByPolicyVersion({
                policyVersionId: config.policyVersionId,
                bodyCreateRunByPolicyVersion: body,
                projectId: config.projectId,
            })
            .then((data) => {
                setError(null);
                setCreatedRun(data);
                return data;
            })
            .catch((error) => {
                console.error("Form launch failed:", error);
                setCreatedRun(null);
                setError(error);
            })
            .finally(() => {
                setSubmitting(false);
            });
    }

    return (
        <LaunchRunFormCard
            form={form}
            onSubmit={onSubmit}
            submitting={submitting}
            setDefaults={setDefaults}
        />
    );
}

function LaunchRunFormCard({
    form,
    onSubmit,
    submitting,
    setDefaults,
}: {
    form: UseFormReturn<z.infer<typeof formSchema>>;
    onSubmit: (values: z.infer<typeof formSchema>) => void;
    submitting: boolean;
    setDefaults: () => void;
}) {
    const placeholderText = JSON.stringify({ string_field: "value1", numeric_field: 1 }, null, 2);
    const hasErrors = Object.keys(form.formState.errors).length > 0;
    const isDirty = form.formState.isDirty;

    return (
        <div className="space-y-6">
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                        <FormField
                            control={form.control}
                            name="input_data"
                            render={({ field }) => (
                                <FormItem className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <FormLabel className="text-base font-semibold">
                                            Input Data
                                        </FormLabel>
                                        <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                                            Required
                                        </span>
                                    </div>
                                    <FormControl>
                                        <div className="relative">
                                            <Textarea
                                                className="min-h-56 font-mono text-sm resize-y"
                                                placeholder={placeholderText}
                                                {...field}
                                            />
                                            <div
                                                className={
                                                    "absolute bottom-3 right-3 text-xs text-muted-foreground " +
                                                    "bg-background/80 px-2 py-1 rounded backdrop-blur-sm"
                                                }
                                            >
                                                {field.value?.length || 0} chars
                                            </div>
                                        </div>
                                    </FormControl>
                                    <FormDescription className="text-sm text-muted-foreground">
                                        JSON data passed to the policy run. Must match the expected
                                        input schema.
                                    </FormDescription>
                                    <FormMessage className="text-sm" />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="config_variables"
                            render={({ field }) => (
                                <FormItem className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <FormLabel className="text-base font-semibold">
                                            Configuration Variables
                                        </FormLabel>
                                        <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                                            Optional
                                        </span>
                                    </div>
                                    <FormControl>
                                        <div className="relative">
                                            <Textarea
                                                className="min-h-56 font-mono text-sm resize-y"
                                                placeholder={placeholderText}
                                                name={field.name}
                                                onBlur={field.onBlur}
                                                onChange={field.onChange}
                                                ref={field.ref}
                                                value={field.value ?? ""}
                                            />
                                            <div
                                                className={
                                                    "absolute bottom-3 right-3 text-xs text-muted-foreground " +
                                                    "bg-background/80 px-2 py-1 rounded backdrop-blur-sm"
                                                }
                                            >
                                                {field.value?.length || 0} chars
                                            </div>
                                        </div>
                                    </FormControl>
                                    <FormDescription className="text-sm text-muted-foreground">
                                        Optional configuration overrides for this specific run.
                                    </FormDescription>
                                    <FormMessage className="text-sm" />
                                </FormItem>
                            )}
                        />
                    </div>

                    {hasErrors && (
                        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 space-y-2">
                            <div className="flex items-center gap-2 text-destructive">
                                <AlertCircle className="h-4 w-4" />
                                <span className="font-medium">
                                    Please fix the following errors:
                                </span>
                            </div>
                            <ul className="list-disc list-inside text-sm text-destructive/80 space-y-1">
                                {Object.entries(form.formState.errors).map(([field, error]) => (
                                    <li key={field}>{error?.message}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div
                        className={
                            "flex flex-col sm:flex-row justify-between items-start " +
                            "sm:items-center gap-4 pt-6 border-t"
                        }
                    >
                        <div className="flex items-center gap-2">
                            <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={setDefaults}
                                disabled={submitting}
                            >
                                <Settings className="h-4 w-4 mr-2" />
                                Reset to Defaults
                            </Button>
                            {isDirty && (
                                <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                                    Unsaved changes
                                </span>
                            )}
                        </div>

                        <Button
                            type="submit"
                            disabled={submitting || hasErrors}
                            className="min-w-[140px]"
                        >
                            {submitting ? (
                                <Sending text="Launching..." />
                            ) : (
                                <>
                                    <Play className="h-4 w-4 mr-2" />
                                    <span>Launch Run</span>
                                </>
                            )}
                        </Button>
                    </div>
                </form>
            </Form>
        </div>
    );
}

function ensureJSON(data: string | null) {
    if (!data) {
        return false;
    }

    try {
        JSON.parse(data);
        return true;
    } catch (e) {
        return false;
    }
}

function asInputData(inputSchema: Record<string, string>) {
    if (!inputSchema) {
        return {};
    }

    const defaultValuePerType = Object.fromEntries([
        ["str", ""],
        ["int", 0],
        ["float", 0.0],
        ["boolean", false],
        ["dict", {}],
        ["list", []],
    ]);
    return Object.fromEntries(
        Object.entries(inputSchema).map(([key, value]) => {
            return [key, defaultValuePerType[value]];
        }),
    );
}

function asConfigMap(configVariables: string[]) {
    if (!configVariables) {
        return {};
    }

    return Object.fromEntries(configVariables.map((key) => [key, ""]));
}

function RunCreatedCard({ createdRun, closeDialog }: { createdRun: RunCreated; closeDialog: () => void }) {
    return (
        <div className="text-center space-y-6 py-8">
            <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-foreground" />
            </div>

            <div className="space-y-3">
                <h3 className="text-xl font-semibold">Run Launched Successfully!</h3>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                    Your policy run has been created and is now executing. You can monitor its
                    progress from the runs page.
                </p>
                <div className="inline-flex items-center gap-2 bg-muted border rounded-lg px-3 py-2">
                    <span className="text-xs font-medium">Run ID:</span>
                    <code className="text-xs font-mono bg-background px-2 py-1 rounded border">
                        {createdRun.run_id}
                    </code>
                </div>
            </div>

            <div className="flex justify-center gap-3 pt-2">
                <Link
                    href={`/policyVersions/${createdRun.policy_version_id}/runs/${createdRun.run_id}`}
                >
                    <Button onClick={closeDialog}>
                        <Play className="h-4 w-4 mr-2" />
                        View Run Details
                    </Button>
                </Link>
                <Button variant="outline" onClick={closeDialog}>
                    Close
                </Button>
            </div>
        </div>
    );
}

function RunCreationErrorCard({ error, onRetry }: { error: Error; onRetry: () => void }) {
    return (
        <div className="text-center space-y-6 py-8">
            <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center">
                <AlertCircle className="w-8 h-8 text-destructive" />
            </div>

            <div className="space-y-3">
                <h3 className="text-xl font-semibold">Launch Failed</h3>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                    There was an error starting your policy run. Please review the error details
                    below and try again.
                </p>
            </div>

            <div className="bg-muted border rounded-lg p-4 text-left max-w-lg mx-auto">
                <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    Error Details
                </h4>
                <div className="bg-background rounded border p-3">
                    <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-32 font-mono text-muted-foreground">
                        {error.message}
                    </pre>
                </div>
            </div>

            <div className="flex justify-center gap-3 pt-2">
                <Button variant="outline" onClick={onRetry}>
                    <Settings className="h-4 w-4 mr-2" />
                    Try Again
                </Button>
                <Button variant="ghost" onClick={() => window.history.back()}>
                    Go Back
                </Button>
            </div>
        </div>
    );
}
