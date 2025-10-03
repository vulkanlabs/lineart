"use client";

import { useState } from "react";
import type { DataSource } from "@vulkanlabs/client-open";
import { TestConfigPanel } from "./TestConfigPanel";
import { TestResponsePanel } from "./TestResponsePanel";

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
}

/**
 * Main test panel component with split view
 * Left: Test configuration
 * Right: Test response
 */
export function TestDataSourcePanel({
    dataSource,
    testDataSource,
    projectId,
}: TestDataSourcePanelProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [response, setResponse] = useState<any>(null);

    const handleTest = async (config: { configured_params: any; override_env_vars?: any }) => {
        if (!testDataSource) throw new Error("Test function not provided");

        setIsLoading(true);
        try {
            const result = await testDataSource(
                dataSource.data_source_id,
                config,
                projectId,
            );
            setResponse(result);
        } catch (error: any) {
            // Handle error by creating error response
            setResponse({
                status_code: 0,
                response_body: null,
                response_time_ms: 0,
                cache_hit: false,
                headers: {},
                request_url: dataSource.source?.url || "",
                error_message: error.message || "An unknown error occurred",
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
            <TestConfigPanel onTest={handleTest} isLoading={isLoading} />
            <TestResponsePanel response={response} isLoading={isLoading} />
        </div>
    );
}
