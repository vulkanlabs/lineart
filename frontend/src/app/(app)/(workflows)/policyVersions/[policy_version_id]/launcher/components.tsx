"use client";

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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { CurrentUser } from "@stackframe/stack";
import { Textarea } from "@/components/ui/textarea";

const formSchema = z.object({
    input_data: z.string().refine(ensureJSON, { message: "Not a valid JSON object" }),
    config_variables: z
        .string()
        .nullable()
        .refine(ensureJSON, { message: "Not a valid JSON object" }),
});

type LaunchRunFormProps = {
    user: CurrentUser;
    policy_version_id: string;
    defaultInputData: Object;
    defaultConfigVariables: Object;
    setCreatedRun: (run: any) => void;
    setError: (error: any) => void;
};

export function LaunchRunForm({
    user,
    policy_version_id,
    defaultInputData,
    defaultConfigVariables,
    setCreatedRun,
    setError,
}: LaunchRunFormProps) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const launchUrl = `${serverUrl}/policyVersions/${policy_version_id}/runs`;

    const form = useForm({
        resolver: zodResolver(formSchema),
        defaultValues: {
            input_data: "",
            config_variables: "",
        },
    });

    const setDefaults = () => {
        form.setValue("input_data", JSON.stringify(defaultInputData, null, 4));
        form.setValue("config_variables", JSON.stringify(defaultConfigVariables, null, 4));
    };

    const [submitting, setSubmitting] = useState(false);

    async function onSubmit(values: z.infer<typeof formSchema>) {
        const { accessToken, refreshToken } = await user.getAuthJson();
        const headers = {
            "x-stack-access-token": accessToken,
            "x-stack-refresh-token": refreshToken,
            "Content-Type": "application/json",
        };

        const body = {
            input_data: JSON.parse(values.input_data),
            config_variables: JSON.parse(values.config_variables),
        };

        setSubmitting(true);
        return fetch(launchUrl, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(body),
            mode: "cors",
        })
            .then(async (response) => {
                if (!response.ok) {
                    const responseBody = await response.json();
                    if (responseBody?.detail) {
                        const errorMsg = responseBody.detail.msg.replace(
                            "Failed to launch run: Failed to trigger job: ",
                            "",
                        ).replaceAll('"', '\\"').replaceAll("'", '"');
                        const splicedError = "[" + errorMsg.substring(1, errorMsg.length - 1) + "]";
                        const errorObj = JSON.parse(splicedError);
                        const errorObjAsString = JSON.stringify(errorObj, null, 2);

                        throw new Error(errorObjAsString);
                    }

                    throw new Error("Failed to create Run: " + response, { cause: response });
                }
                const data = await response.json();
                setCreatedRun(data);
                setError(null);
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
                                Launch Run
                            </Button>
                            {submitting && <p>Submitting...</p>}
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
