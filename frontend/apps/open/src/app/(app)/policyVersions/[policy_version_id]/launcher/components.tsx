"use client";

// React and Next.js
import { useState } from "react";
import Link from "next/link";

// External libraries
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, UseFormReturn } from "react-hook-form";
import { Play, Settings } from "lucide-react";

// Vulkan packages
import {
    Button,
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
    Textarea,
} from "@vulkanlabs/base/ui";
import { Sending } from "@vulkanlabs/base";
import { Run } from "@vulkanlabs/client-open";

// Local imports
import { LauncherFnParams } from "./types";

type LauncherPageProps = {
    policyVersionId: string;
    inputSchema: Map<string, string>;
    configVariables?: string[];
    launchFn: any;
};

export function LauncherPage({
    policyVersionId,
    inputSchema,
    configVariables,
    launchFn,
}: LauncherPageProps) {
    const [createdRun, setCreatedRun] = useState(null);
    const [error, setError] = useState<Error | null>(null);

    return (
        <div className="flex flex-col p-8 gap-8">
            <h1 className="text-2xl font-bold tracking-tight">Launcher</h1>
            <div>
                <LaunchRunForm
                    policyVersionId={policyVersionId}
                    setCreatedRun={setCreatedRun}
                    setError={setError}
                    defaultInputData={asInputData(inputSchema)}
                    defaultConfigVariables={asConfigMap(configVariables || [])}
                    launchFn={launchFn}
                />
            </div>
            {createdRun && (
                <RunCreatedCard createdRun={createdRun} closeDialog={() => setCreatedRun(null)} />
            )}
            {error && <RunCreationErrorCard error={error} />}
        </div>
    );
}

export function LauncherButton({
    policyVersionId,
    inputSchema,
    configVariables,
    launchFn,
}: LauncherPageProps) {
    const [isQuickLaunching, setIsQuickLaunching] = useState(false);

    const handleQuickLaunch = async () => {
        setIsQuickLaunching(true);
        
        try {
            const defaultBody = {
                input_data: asInputData(inputSchema),
                config_variables: asConfigMap(configVariables || []),
            };

            const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
            const launchUrl = `${serverUrl}/policy-versions/${policyVersionId}/runs`;
            
            await launchFn({ launchUrl, body: defaultBody, headers: {} });
            
        } catch (error) {
            console.error("Launch failed:", error);
        } finally {
            setIsQuickLaunching(false);
        }
    };

    return (
        <Button 
            onClick={handleQuickLaunch}
            disabled={isQuickLaunching}
            variant="outline"
            className="border-input bg-background hover:bg-accent hover:text-accent-foreground"
        >
            {isQuickLaunching ? (
                <Sending text="Launching..." />
            ) : (
                <>
                    <Play className="h-4 w-4 mr-2" />
                    Launch Run
                </>
            )}
        </Button>
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
    policyVersionId: string;
    defaultInputData: Object;
    defaultConfigVariables: Object;
    setCreatedRun: (run: any) => void;
    setError: (error: any) => void;
    launchFn: (params: LauncherFnParams) => Promise<Run>;
};

function LaunchRunForm({
    policyVersionId,
    defaultInputData,
    defaultConfigVariables,
    setCreatedRun,
    setError,
    launchFn,
}: LaunchRunFormProps) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const launchUrl = `${serverUrl}/policy-versions/${policyVersionId}/runs`;

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            input_data: JSON.stringify(defaultInputData, null, 4),
            config_variables: JSON.stringify(defaultConfigVariables, null, 4),
        },
    });

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
        launchFn({ launchUrl, body, headers: {} })
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
    return (
        <div className="space-y-6">
            <div className="space-y-2">
                <h2 className="text-xl font-semibold tracking-tight">Configure Launch Parameters</h2>
                <p className="text-sm text-muted-foreground">
                    Customize input data and configuration variables for this run
                </p>
            </div>
            
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <FormField
                            control={form.control}
                            name="input_data"
                            render={({ field }) => (
                                <FormItem className="space-y-3">
                                    <FormLabel className="text-base font-medium">Input Data</FormLabel>
                                    <FormControl>
                                        <Textarea
                                            className="min-h-48 font-mono text-sm resize-none border-2 focus:border-blue-500 transition-colors"
                                            placeholder={placeholderText}
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormDescription className="text-sm">
                                        JSON data that will be passed to the policy run. Must match the expected input schema.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="config_variables"
                            render={({ field }) => (
                                <FormItem className="space-y-3">
                                    <FormLabel className="text-base font-medium">Configuration Variables</FormLabel>
                                    <FormControl>
                                        <Textarea
                                            className="min-h-48 font-mono text-sm resize-none border-2 focus:border-blue-500 transition-colors"
                                            placeholder={placeholderText}
                                            value={field.value || ""}
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormDescription className="text-sm">
                                        Optional configuration overrides for this specific run.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                    </div>
                    
                    <div className="flex flex-row justify-between items-center pt-4 border-t">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={setDefaults}
                            disabled={submitting}
                            className="flex items-center gap-2 border-input bg-background hover:bg-accent hover:text-accent-foreground"
                        >
                            <Settings className="h-4 w-4" />
                            Reset to Defaults
                        </Button>
                        
                        <div className="flex gap-3">
                            <Button
                                type="submit"
                                disabled={submitting}
                                variant="outline"
                                className="min-w-[120px] border-input bg-background hover:bg-accent hover:text-accent-foreground"
                            >
                                {submitting ? (
                                    <Sending text="Launching..." />
                                ) : (
                                    <>
                                        <Play className="h-4 w-4 mr-2" />
                                        Launch Run
                                    </>
                                )}
                            </Button>
                        </div>
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

function asInputData(inputSchema: Map<string, string>) {
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

function RunCreatedCard({ createdRun, closeDialog }: { createdRun: Run; closeDialog: () => void }) {
    return (
        <div className="text-center space-y-6 py-6">
            <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <div className="w-6 h-6 bg-green-500 rounded-full"></div>
            </div>
            
            <div className="space-y-2">
                <h3 className="text-lg font-semibold">Run Launched Successfully!</h3>
                <p className="text-sm text-muted-foreground">
                    Your policy run has been started and is now executing.
                </p>
                <p className="text-xs text-muted-foreground font-mono bg-muted px-2 py-1 rounded">
                    Run ID: {createdRun.run_id}
                </p>
            </div>
            
            <div className="flex justify-center gap-3">
                <Link href={`/policyVersions/${createdRun.policy_version_id}/runs/${createdRun.run_id}`}>
                    <Button 
                        onClick={closeDialog}
                        className="bg-primary text-primary-foreground hover:bg-primary/90"
                    >
                        View Run Details
                    </Button>
                </Link>
                <Button 
                    variant="outline" 
                    onClick={closeDialog}
                    className="border-input bg-background hover:bg-accent hover:text-accent-foreground"
                >
                    Close
                </Button>
            </div>
        </div>
    );
}

function RunCreationErrorCard({ error }: { error: Error }) {
    return (
        <div className="text-center space-y-6 py-6">
            <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <div className="w-6 h-6 bg-red-500 rounded-full"></div>
            </div>
            
            <div className="space-y-2">
                <h3 className="text-lg font-semibold">Launch Failed</h3>
                <p className="text-sm text-muted-foreground">
                    There was an error starting your policy run.
                </p>
            </div>
            
            <div className="bg-muted border rounded-lg p-3 text-left">
                <h4 className="text-sm font-medium mb-2">Error Details:</h4>
                <pre className="text-xs text-muted-foreground whitespace-pre-wrap overflow-auto max-h-24">
                    {error.message}
                </pre>
            </div>
            
            <div className="flex justify-center gap-3">
                <Button 
                    variant="outline" 
                    onClick={() => window.location.reload()}
                    className="border-input bg-background hover:bg-accent hover:text-accent-foreground"
                >
                    Try Again
                </Button>
                <Button 
                    variant="outline" 
                    onClick={() => window.history.back()}
                    className="border-input bg-background hover:bg-accent hover:text-accent-foreground"
                >
                    Go Back
                </Button>
            </div>
        </div>
    );
}
