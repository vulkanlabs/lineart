"use client";
import Link from "next/link";
import React, { useState } from "react";
import { useUser } from "@stackframe/stack";
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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export async function BacktestLauncherPage({ policyVersionId, launchFn, uploadedFiles }) {
    const [error, setError] = useState<Error>(null);
    const [backtestId, setBacktestId] = useState<string | null>(null);

    const user = useUser();
    const authJson = await user.getAuthJson();
    const headers = {
        "x-stack-access-token": authJson.accessToken,
        "x-stack-refresh-token": authJson.refreshToken,
    };

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
                    headers={headers}
                />
            </div>
            {backtestId && <LaunchCard backtestId={backtestId} policyVersionId={policyVersionId} />}
            {error && <LaunchErrorCard error={error} />}
        </div>
    );
}

const formSchema = z.object({
    input_file_id: z.string(),
    enable_metrics: z.boolean(),
    config_variables: z.string().refine(ensureJSON, { message: "Not a valid JSON object" }),
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
        defaultValues: {
            config_variables: "",
        },
    });

    async function onSubmit(values: z.infer<typeof formSchema>) {
        const body = {
            input_file_id: values.input_file_id,
            // enable_metrics: values.enable_metrics,
            config_variables: JSON.parse(values.config_variables),
            policy_version_id: policyVersionId,
        };

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

function LaunchFormCard({ uploadedFiles, form, onSubmit, submitting }) {
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
                                                    {file.uploaded_file_id}
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
                                            className="min-h-40"
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
                        <FormField
                            control={form.control}
                            name="enable_metrics"
                            render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                    <div className="space-y-0.5">
                                        <FormLabel className="text-base">Enable Metrics</FormLabel>
                                        <FormDescription>
                                            Automatically generate metrics and visualizations for
                                            the outcomes of the backtest.
                                        </FormDescription>
                                    </div>
                                    <FormControl>
                                        <Switch
                                            checked={field.value}
                                            onCheckedChange={field.onChange}
                                        />
                                    </FormControl>
                                </FormItem>
                            )}
                        />
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

function ensureJSON(data: string) {
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
    console.log(error);
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
