"use client";
import Link from "next/link";
import React, { useState } from "react";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
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
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { AuthHeaders } from "@/lib/auth";

export function BacktestLauncherPage({
    authHeaders,
    policyVersionId,
    launchFn,
    uploadedFiles,
}: {
    authHeaders: AuthHeaders;
    policyVersionId: string;
    launchFn: any;
    uploadedFiles: any;
}) {
    const [error, setError] = useState<Error>(null);
    const [backtestId, setBacktestId] = useState<string | null>(null);

    return (
        <div className="flex flex-col py-4 px-8 gap-8">
            <Link href={`/policyVersions/${policyVersionId}/backtests`}>
                <button className="flex flex-row gap-2 bg-white text-black hover:text-gray-700 text-lg font-bold">
                    <ArrowLeft />
                    Back
                </button>
            </Link>
            <div>
                <BacktestLauncher
                    policyVersionId={policyVersionId}
                    uploadedFiles={uploadedFiles}
                    setBacktestId={setBacktestId}
                    setError={setError}
                    launchFn={launchFn}
                    headers={authHeaders}
                />
            </div>
            {backtestId && <LaunchCard backtestId={backtestId} policyVersionId={policyVersionId} />}
            {error && <LaunchErrorCard error={error} />}
        </div>
    );
}

const formSchema = z.object({
    input_file_id: z.string(),
    config_variables: z
        .string()
        .optional()
        .refine(ensureJSON, { message: "Not a valid JSON object" }),
    target_column: z.string().optional(),
    time_column: z.string().optional(),
    group_by_columns: z.string().optional(),
});

function BacktestLauncher({
    policyVersionId,
    uploadedFiles,
    setBacktestId,
    setError,
    launchFn,
    headers,
}) {
    const [submitting, setSubmitting] = useState(false);

    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const uploadUrl = `${serverUrl}/backtests/`;

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
    });

    async function onSubmit(values: z.infer<typeof formSchema>) {
        const body = {
            input_file_id: values.input_file_id,
            policy_version_id: policyVersionId,
            config_variables: null,
            metrics_config: null,
        };

        if (values.config_variables) {
            body.config_variables = JSON.parse(values.config_variables);
        }

        if (values.target_column) {
            let metricsConfig = {
                target_column: values.target_column,
                time_column: null,
                group_by_columns: null,
            };
            if (values.time_column) {
                metricsConfig.time_column = values.time_column;
            }
            if (values.group_by_columns) {
                metricsConfig.group_by_columns = values.group_by_columns
                    .split(",")
                    .map((s) => s.trim());
            }
            body.metrics_config = metricsConfig;
        }

        setSubmitting(true);
        setError(null);
        setBacktestId(null);

        launchFn({ uploadUrl, body, headers })
            .then((data) => {
                setError(null);
                setBacktestId(data.backtest_id);
            })
            .catch((error) => {
                setError(error);
            })
            .finally(() => {
                setSubmitting(false);
            });
    }

    return (
        <LaunchFormCard
            uploadedFiles={uploadedFiles}
            form={form}
            onSubmit={onSubmit}
            submitting={submitting}
        />
    );
}

function FileInfoRow({ uploaded_file_id, created_at }) {
    return (
        <div className="flex flex-row justify-between">
            <div>
                <div className="font-semibold">{uploaded_file_id}</div>
                <div className="text-sm text-muted-foreground">{created_at}</div>
            </div>
        </div>
    );
}

function LaunchFormCard({ uploadedFiles, form, onSubmit, submitting }) {
    const [enableMetrics, setEnableMetrics] = useState(false);
    const placeholderText = JSON.stringify([{ variable: "value" }], null, 2);

    return (
        <Card>
            <CardHeader>
                <CardTitle>Launch Backtest</CardTitle>
                <CardDescription>Launch a backtest job.</CardDescription>
            </CardHeader>
            <CardContent>
                <Form {...form}>
                    <form className="flex flex-col gap-4" onSubmit={form.handleSubmit(onSubmit)}>
                        <FormField
                            control={form.control}
                            name="input_file_id"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Input File</FormLabel>
                                    <Select
                                        onValueChange={field.onChange}
                                        defaultValue={field.value}
                                    >
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select an input file" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            {uploadedFiles.map((file) => (
                                                <SelectItem
                                                    key={file.uploaded_file_id}
                                                    value={file.uploaded_file_id}
                                                >
                                                    <FileInfoRow {...file} />
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <FormDescription>
                                        ID of the uploaded file to be used as input.
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
                                    <FormLabel>Config Variables</FormLabel>
                                    <FormControl>
                                        <Textarea
                                            className="min-h-32"
                                            placeholder={placeholderText}
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormDescription>
                                        List of configurations for the backtest.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <div className="flex flex-col gap-6 rounded-lg border p-4">
                            <div className="flex flex-row items-center justify-between">
                                <div className="space-y-0.5">
                                    <div className="text-base font-medium">Metrics</div>
                                    <div className="text-sm text-muted-foreground">
                                        Automatically generate metrics and visualizations for the
                                        outcomes of the backtest.
                                    </div>
                                </div>
                                <div>
                                    <Switch
                                        checked={enableMetrics}
                                        onCheckedChange={setEnableMetrics}
                                    />
                                </div>
                            </div>
                            {enableMetrics && <MetricsForm form={form} />}
                        </div>
                        <div className="flex flex-row gap-4">
                            <Button type="submit" disabled={submitting}>
                                Launch
                            </Button>
                            {submitting && <p>Submitting...</p>}
                        </div>
                    </form>
                </Form>
            </CardContent>
        </Card>
    );
}

function MetricsForm({ form }) {
    return (
        <>
            <FormField
                control={form.control}
                name="target_column"
                render={({ field }) => (
                    <FormItem>
                        <FormLabel>Target Column</FormLabel>
                        <FormControl>
                            <Input type="text" {...field} />
                        </FormControl>
                        <FormDescription>Name of the column to use as a target.</FormDescription>
                        <FormMessage />
                    </FormItem>
                )}
            />
            <FormField
                control={form.control}
                name="time_column"
                render={({ field }) => (
                    <FormItem>
                        <FormLabel>Time Column (optional)</FormLabel>
                        <FormControl>
                            <Input type="text" {...field} />
                        </FormControl>
                        <FormDescription>Name of the column to use as a time step.</FormDescription>
                        <FormMessage />
                    </FormItem>
                )}
            />
            <FormField
                control={form.control}
                name="group_by_columns"
                render={({ field }) => (
                    <FormItem>
                        <FormLabel>Group By Columns (optional)</FormLabel>
                        <FormControl>
                            <Input type="text" placeholder="first,second,third" {...field} />
                        </FormControl>
                        <FormDescription>
                            Names of the columns to group results by (comma-separated).
                        </FormDescription>
                        <FormMessage />
                    </FormItem>
                )}
            />
        </>
    );
}

function ensureJSON(data: string | null) {
    if (!data) {
        return true;
    }
    try {
        JSON.parse(data);
        return true;
    } catch (e) {
        return false;
    }
}

function LaunchCard({ backtestId, policyVersionId }) {
    return (
        <Card className="flex flex-col w-fit border-green-600 border-2">
            <CardHeader>
                <CardTitle>Launched backtest successfully</CardTitle>
                <CardDescription className="flex flex-col gap-4">
                    <div>
                        Backtest launched with id <strong>{backtestId}</strong>.
                    </div>
                    <Link href={`/policyVersions/${policyVersionId}/backtests`}>
                        <Button className="bg-green-600 hover:bg-green-500">Go to Table</Button>
                    </Link>
                </CardDescription>
            </CardHeader>
        </Card>
    );
}

function LaunchErrorCard({ error }) {
    return (
        <Card className="flex flex-col w-fit border-red-600 border-2">
            <CardHeader>
                <CardTitle>Failed to launch backtest</CardTitle>
                <CardDescription>
                    Error during launch: <br />
                </CardDescription>
            </CardHeader>
            <CardContent>
                <pre className="text-wrap">{error.message}</pre>
            </CardContent>
        </Card>
    );
}
