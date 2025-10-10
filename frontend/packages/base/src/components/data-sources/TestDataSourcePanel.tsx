"use client";

import { useState, useRef } from "react";
import type { DataSource } from "@vulkanlabs/client-open";
import { TestConfigPanel, type TestConfigPanelRef } from "./TestConfigPanel";
import { TestResponsePanel } from "./TestResponsePanel";
import { Button, Separator } from "../ui";
import { Play } from "lucide-react";

interface TestConfig {
    configuredParams: Record<string, string>;
    overrideEnvVars: Record<string, string>;
    customParams: Array<{ key: string; value: string }>;
    customEnvVars: Array<{ key: string; value: string }>;
}

interface TestDataSourcePanelProps {
    dataSource: DataSource;
    testDataSource?: (
        dataSourceId: string,
        testRequest: {
            configured_params: any;
            override_env_vars?: any;
        },
        projectId?: string,
    ) => Promise<{
        status_code: number;
        response_body: any;
        response_time_ms: number;
        cache_hit: boolean;
        headers: Record<string, string>;
        request_url: string;
        error_message?: string;
    }>;
    projectId?: string;
    testConfig?: TestConfig;
    onTestConfigChange?: (config: TestConfig) => void;
}

/**
 * Main test panel component with unified layout matching the general tab
 */
export function TestDataSourcePanel({
    dataSource,
    testDataSource,
    projectId,
    testConfig: externalTestConfig,
    onTestConfigChange,
}: TestDataSourcePanelProps) {
    const testConfigPanelRef = useRef<TestConfigPanelRef>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [response, setResponse] = useState<any>(null);

    // Use external config if provided, or use local state
    const [localTestConfig, setLocalTestConfig] = useState<TestConfig>({
        configuredParams: {},
        overrideEnvVars: {},
        customParams: [],
        customEnvVars: [],
    });

    const testConfig = externalTestConfig ?? localTestConfig;
    const setTestConfig = onTestConfigChange ?? setLocalTestConfig;

    const handleTest = async (config: { configured_params: any; override_env_vars?: any }) => {
        if (!testDataSource) throw new Error("Test function not provided");

        setIsLoading(true);
        try {
            const result = await testDataSource(dataSource.data_source_id, config, projectId);
            setResponse(result);
        } catch (error: any) {
            // Extract status code from error if available
            const statusCode = error.response?.status || error.status || 500;

            // Determine error message based on error type
            let errorMessage = error.message || "An unknown error occurred";

            if (error.name === 'TypeError' && error.message.includes('fetch'))
                errorMessage = "Network error: Unable to connect to the data source";
            else if (error.name === 'AbortError' || error.message.includes('timeout'))
                errorMessage = "Request timeout: The data source took too long to respond";

            // Handle error by creating error response
            setResponse({
                status_code: statusCode,
                response_body: error.response?.data || null,
                response_time_ms: 0,
                cache_hit: false,
                headers: error.response?.headers || {},
                request_url: dataSource.source?.url || "",
                error_message: errorMessage,
            });
        } finally {
            setIsLoading(false);
        }
    };

    // Check if theres enough information to run the test
    const validateTestConfig = () => {
        const errors: string[] = [];

        // Check if the data source has a valid URL configured
        if (!dataSource.source?.url || dataSource.source.url.trim() === "")
            errors.push("URL is not configured");

        // Collect all non-empty values
        const allValues: string[] = [
            // Configured runtime params values
            ...Object.values(testConfig.configuredParams).filter(v => v && v.trim() !== ""),
            // Custom params values
            ...testConfig.customParams
                .filter(p => p.key.trim() !== "" && p.value.trim() !== "")
                .map(p => p.value),
            // Override env vars values
            ...Object.values(testConfig.overrideEnvVars).filter(v => v && v.trim() !== ""),
            // Custom env vars values
            ...testConfig.customEnvVars
                .filter(e => e.key.trim() !== "" && e.value.trim() !== "")
                .map(e => e.value),
        ];

        // Check if at least one non empty value exists
        if (allValues.length === 0) errors.push("At least one parameter or environment variable value is required");

        return {
            isValid: errors.length === 0,
            errors,
        };
    };

    const handleRunTest = () => {
        const validation = validateTestConfig();

        if (!validation.isValid) {
            // button should be disabled
            const errorMessage = validation.errors.join(". ");
            console.warn("Test validation failed:", errorMessage);
            return;
        }

        testConfigPanelRef.current?.submit();
    };

    const validation = validateTestConfig();
    const isTestDisabled = isLoading || !validation.isValid;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-semibold md:text-2xl">Test Data Source</h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        Test your data source with custom parameters and environment variables
                    </p>
                </div>
                <Button onClick={handleRunTest} disabled={isTestDisabled}>
                    <Play className="h-4 w-4 mr-2" />
                    {isLoading ? "Running..." : "Run Test"}
                </Button>
            </div>

            <Separator />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="border border-border rounded-lg p-6 bg-card">
                    <TestConfigPanel
                        ref={testConfigPanelRef}
                        dataSource={dataSource}
                        onTest={handleTest}
                        isLoading={isLoading}
                        initialConfig={testConfig}
                        onConfigChange={setTestConfig}
                    />
                </div>
                <div className="border border-border rounded-lg p-6 bg-card">
                    <TestResponsePanel response={response} isLoading={isLoading} />
                </div>
            </div>
        </div>
    );
}
