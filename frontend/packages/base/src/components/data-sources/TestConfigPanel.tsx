"use client";

import { useState } from "react";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Play } from "lucide-react";
import {
    Button,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
    Textarea,
} from "../ui";

const testConfigSchema = z.object({
    configured_params: z.string().optional(),
    override_env_vars: z.string().optional(),
});

interface TestConfigPanelProps {
    onTest: (config: { configured_params: any; override_env_vars?: any }) => Promise<void>;
    isLoading?: boolean;
}

/**
 * Left panel component for configuring test parameters
 * Allows users to provide runtime params and override environment variables
 */
export function TestConfigPanel({ onTest, isLoading }: TestConfigPanelProps) {
    const [testError, setTestError] = useState<string | null>(null);

    const form = useForm<z.infer<typeof testConfigSchema>>({
        resolver: zodResolver(testConfigSchema),
        defaultValues: {
            configured_params: "",
            override_env_vars: "",
        },
    });

    const onSubmit = async (data: z.infer<typeof testConfigSchema>) => {
        setTestError(null);
        try {
            let configured_params = {};
            let override_env_vars = undefined;

            // Parse configured params
            if (data.configured_params?.trim())
                try {
                    configured_params = JSON.parse(data.configured_params);
                } catch (e) {
                    setTestError("Invalid JSON in Configured Parameters");
                    return;
                }

            // Parse override env vars
            if (data.override_env_vars?.trim())
                try {
                    override_env_vars = JSON.parse(data.override_env_vars);
                } catch (e) {
                    setTestError("Invalid JSON in Override Environment Variables");
                    return;
                }

            await onTest({ configured_params, override_env_vars });
        } catch (error: any) {
            setTestError(error.message || "Failed to run test");
        }
    };

    const configuredParamsPlaceholder = JSON.stringify(
        {
            user_id: "123",
            filter: "active",
        },
        null,
        2,
    );

    const envVarsPlaceholder = JSON.stringify(
        {
            API_KEY: "test-key-123",
            BASE_URL: "https://staging.api.example.com",
        },
        null,
        2,
    );

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle>Test Configuration</CardTitle>
            </CardHeader>
            <CardContent>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        <FormField
                            control={form.control}
                            name="configured_params"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Configured Parameters</FormLabel>
                                    <FormDescription>
                                        Runtime parameters in JSON format (optional)
                                    </FormDescription>
                                    <FormControl>
                                        <Textarea
                                            {...field}
                                            placeholder={configuredParamsPlaceholder}
                                            className="font-mono text-sm min-h-24"
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="override_env_vars"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Override Environment Variables</FormLabel>
                                    <FormDescription>
                                        Override env vars for testing in JSON format (optional)
                                    </FormDescription>
                                    <FormControl>
                                        <Textarea
                                            {...field}
                                            placeholder={envVarsPlaceholder}
                                            className="font-mono text-sm min-h-24"
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {testError && (
                            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                                <div className="text-sm text-destructive">{testError}</div>
                            </div>
                        )}

                        <Button type="submit" disabled={isLoading} className="w-full">
                            <Play className="h-4 w-4 mr-2" />
                            {isLoading ? "Running Test..." : "Run Test"}
                        </Button>
                    </form>
                </Form>
            </CardContent>
        </Card>
    );
}
