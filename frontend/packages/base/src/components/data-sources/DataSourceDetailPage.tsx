"use client";

import { Suspense, useState } from "react";

// Vulkan packages
import type { DataSource, DataSourceEnvVarBase } from "@vulkanlabs/client-open";

// Local components
import { Separator, Tabs, TabsContent, TabsList, TabsTrigger } from "../ui";
import { Loader } from "../..";

import { useDataSourceUtils } from "./useDataSourceUtils";
import { DataSourceHeader } from "./DataSourceHeader";
import { EditableVariablesCard } from "./EditableVariablesCard";
import { DataSourceUsageAnalytics, UsageAnalyticsConfig } from "./DataSourceUsageAnalytics";
import { TestDataSourcePanel } from "./TestDataSourcePanel";
import { EditDataSourcePanel } from "./EditDataSourcePanel";

interface TestConfig {
    configuredParams: Record<string, string>;
    overrideEnvVars: Record<string, string>;
    customParams: Array<{ key: string; value: string }>;
    customEnvVars: Array<{ key: string; value: string }>;
}

export interface DataSourceDetailPageConfig {
    dataSource: DataSource;
    updateDataSource: (
        dataSourceId: string,
        updates: Partial<DataSource>,
        projectId?: string,
    ) => Promise<DataSource>;
    fetchDataSourceEnvVars: (
        dataSourceId: string,
        projectId?: string,
    ) => Promise<DataSourceEnvVarBase[]>;
    setDataSourceEnvVars: (
        dataSourceId: string,
        variables: DataSourceEnvVarBase[],
        projectId?: string,
    ) => Promise<void>;
    fetchUsage: (
        dataSourceId: string,
        from: Date,
        to: Date,
        projectId?: string,
    ) => Promise<{
        requests_by_date: any[];
    }>;
    fetchMetrics: (
        dataSourceId: string,
        from: Date,
        to: Date,
        projectId?: string,
    ) => Promise<{
        avg_response_time_by_date: any[];
        error_rate_by_date: any[];
    }>;
    fetchCacheStats: (
        dataSourceId: string,
        from: Date,
        to: Date,
        projectId?: string,
    ) => Promise<{
        cache_hit_ratio_by_date: any[];
    }>;
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
    publishDataSource?: (dataSourceId: string) => Promise<DataSource>;
    projectId?: string;
}

export function DataSourceDetailPage({ config }: { config: DataSourceDetailPageConfig }) {
    return (
        <div className="flex flex-col gap-6 p-6">
            <DataSourceDetails config={config} />
        </div>
    );
}

interface UsageAnalyticsSectionProps {
    dataSourceId: string;
    config: UsageAnalyticsConfig;
}

function UsageAnalyticsSection({ dataSourceId, config }: UsageAnalyticsSectionProps) {
    return (
        <Suspense
            fallback={
                <div className="flex justify-center p-8">
                    <Loader />
                </div>
            }
        >
            <DataSourceUsageAnalytics dataSourceId={dataSourceId} config={config} />
        </Suspense>
    );
}

function DataSourceDetails({ config }: { config: DataSourceDetailPageConfig }) {
    const { dataSource, fetchDataSourceEnvVars, setDataSourceEnvVars, publishDataSource } = config;

    const { copiedField, copyToClipboard, getFullDataSourceJson } = useDataSourceUtils();

    const status = dataSource.status ?? "DRAFT";
    const isPublished = status === "PUBLISHED";

    // State for test configuration and response persists across tab changes
    const [testConfig, setTestConfig] = useState<TestConfig>({
        configuredParams: {},
        overrideEnvVars: {},
        customParams: [],
        customEnvVars: [],
    });

    const [testResponse, setTestResponse] = useState<any>(null);

    return (
        <>
            <DataSourceHeader
                dataSource={dataSource}
                copiedField={copiedField}
                onCopyToClipboard={copyToClipboard}
                onGetFullDataSourceJson={getFullDataSourceJson}
                onPublish={publishDataSource}
                onUpdateDataSource={config.updateDataSource}
                projectId={config.projectId}
            />

            <Separator />

            {/* Main content */}
            <Tabs defaultValue="general" className="w-full">
                <TabsList className="mb-4">
                    <TabsTrigger value="general">General</TabsTrigger>
                    <TabsTrigger value="test">Test</TabsTrigger>
                    <TabsTrigger value="usage">Usage</TabsTrigger>
                </TabsList>

                <TabsContent value="general" className="space-y-8">
                    <EditDataSourcePanel
                        dataSource={dataSource}
                        updateDataSource={config.updateDataSource}
                        projectId={config.projectId}
                        disabled={isPublished}
                    />

                    <EditableVariablesCard
                        dataSource={dataSource}
                        projectId={config.projectId}
                        fetchDataSourceEnvVars={fetchDataSourceEnvVars}
                        setDataSourceEnvVars={setDataSourceEnvVars}
                    />
                </TabsContent>

                <TabsContent value="test">
                    <TestDataSourcePanel
                        dataSource={dataSource}
                        testDataSource={config.testDataSource}
                        projectId={config.projectId}
                        testConfig={testConfig}
                        onTestConfigChange={setTestConfig}
                        testResponse={testResponse}
                        onTestResponseChange={setTestResponse}
                    />
                </TabsContent>

                <TabsContent value="usage">
                    <UsageAnalyticsSection
                        dataSourceId={dataSource.data_source_id}
                        config={config}
                    />
                </TabsContent>
            </Tabs>
        </>
    );
}
