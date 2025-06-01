"use client";
import Link from "next/link";
import { useState } from "react";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
    Form,
    FormField,
    FormControl,
    FormDescription,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";

import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { LauncherFnParams } from "./types";
import { Run } from "@vulkan-server/Run";
import { Play } from "lucide-react";
import { Sending } from "@/components/animations/sending";

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
    const [error, setError] = useState<Error>(null);

    return (
        <div className="flex flex-col p-8 gap-8">
            <h1 className="text-2xl font-bold tracking-tight">Launcher</h1>
            <div>
                <LaunchRunForm
                    policyVersionId={policyVersionId}
                    setCreatedRun={setCreatedRun}
                    setError={setError}
                    defaultInputData={asInputData(inputSchema)}
                    defaultConfigVariables={asConfigMap(configVariables)}
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
    const [createdRun, setCreatedRun] = useState(null);
    const [error, setError] = useState<Error>(null);
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
                <Button variant="outline">
                    <>
                        <Play />
                        <span>Launch Run</span>
                    </>
                </Button>
            </DialogTrigger>
            <DialogTitle className="sr-only">Launch a Run</DialogTitle>
            <DialogContent className="md:max-w-[60%]">
                {!error && !createdRun && (
                    <LaunchRunForm
                        policyVersionId={policyVersionId}
                        launchFn={launchFn}
                        defaultConfigVariables={asConfigMap(configVariables)}
                        defaultInputData={asInputData(inputSchema)}
                        setCreatedRun={setCreatedRun}
                        setError={setError}
                    />
                )}
                {error && <RunCreationErrorCard error={error} />}
                {createdRun && (
                    <RunCreatedCard
                        createdRun={createdRun}
                        closeDialog={() => {
                            handleOpenChange(false);
                        }}
                    />
                )}
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
    policyVersionId: string;
    defaultInputData: Object;
    defaultConfigVariables: Object;
    setCreatedRun: (run: any) => void;
    setError: (error: any) => void;
    launchFn: (LauncherFnParams) => Promise<Run>;
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

    const form = useForm({
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
            config_variables: JSON.parse(values.config_variables),
        };

        setSubmitting(true);
        setError(null);
        setCreatedRun(null);
        launchFn({ launchUrl, body })
            .then((data) => {
                setError(null);
                setCreatedRun(data);

                return data;
            })
            .catch((error) => {
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

function LaunchRunFormCard({ form, onSubmit, submitting, setDefaults }) {
    const placeholderText = JSON.stringify({ string_field: "value1", numeric_field: 1 }, null, 2);
    return (
        <Card>
            <CardHeader>
                <CardTitle>Launch a Run</CardTitle>
                <CardDescription>
                    Configure and launch a run for this Policy Version
                </CardDescription>
            </CardHeader>
            <CardContent>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="grid grid-cols-2 gap-2">
                        <FormField
                            control={form.control}
                            name="input_data"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Input Data</FormLabel>
                                    <FormControl>
                                        <Textarea
                                            className="min-h-40"
                                            placeholder={placeholderText}
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormDescription>
                                        Input data for the run. <br />
                                        Must follow the input schema for the policy.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="config_variables"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Configuration Variables</FormLabel>
                                    <FormControl>
                                        <Textarea
                                            className="min-h-40"
                                            placeholder={placeholderText}
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormDescription>
                                        Configuration variables for the run. <br />
                                        Override any configuration set in the policy version.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <div className="flex flex-row gap-4">
                            <Button type="submit" disabled={submitting}>
                                {submitting ? (
                                    <Sending text={"Launching..."} />
                                ) : (
                                    <span>Launch Run</span>
                                )}
                            </Button>
                            <Button
                                type="button"
                                variant="secondary"
                                onClick={setDefaults}
                                disabled={submitting}
                                className="bg-gray-200 hover:bg-gray-500"
                            >
                                Use Default Values
                            </Button>
                        </div>
                    </form>
                </Form>
            </CardContent>
        </Card>
    );
}

function ensureJSON(data: string) {
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

function RunCreatedCard({ createdRun, closeDialog }) {
    return (
        <Card className="flex flex-col w-fit border-green-600 border-2">
            <CardHeader>
                <CardTitle>Launched run successfully</CardTitle>
                <CardDescription>
                    <Link
                        href={`/policyVersions/${createdRun.policy_version_id}/runs/${createdRun.run_id}`}
                    >
                        <Button className="bg-green-600 hover:bg-green-500" onClick={closeDialog}>
                            View Run
                        </Button>
                    </Link>
                </CardDescription>
            </CardHeader>
        </Card>
    );
}

function RunCreationErrorCard({ error }) {
    return (
        <Card className="flex flex-col w-fit border-red-600 border-2">
            <CardHeader>
                <CardTitle>Failed to launch run</CardTitle>
                <CardDescription>
                    Launch failed with error: <br />
                </CardDescription>
            </CardHeader>
            <CardContent>
                <pre className="text-wrap">{error.message}</pre>
            </CardContent>
        </Card>
    );
}
