"use client";

import { Suspense } from "react";

// Vulkan packages
import type { DataSource, DataSourceEnvVarBase } from "@vulkanlabs/client-open";

// Local components
import { Separator, Tabs, TabsContent, TabsList, TabsTrigger } from "../ui";
import { Loader } from "../..";

import { useDataSourceUtils } from "./useDataSourceUtils";
import { DataSourceHeader } from "./DataSourceHeader";
import { DataSourceSummaryCard } from "./DataSourceSummaryCard";
import { SourceConfigurationCard } from "./SourceConfigurationCard";
import { RetryPolicyCard } from "./RetryPolicyCard";
import { CachingConfigurationCard } from "./CachingConfigurationCard";
import { EditableVariablesCard } from "./EditableVariablesCard";
import { DataSourceUsageAnalytics, UsageAnalyticsConfig } from "./DataSourceUsageAnalytics";

export interface DataSourceDetailPageConfig {
    dataSource: DataSource;
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
    projectId?: string;
}

export function DataSourceDetailPage({ config }: { config: DataSourceDetailPageConfig }) {
    const { dataSource } = config;

    return (
        <div className="flex flex-col gap-6 p-6">
            <DataSourceDetails config={config} />
            <UsageAnalyticsSection dataSourceId={dataSource.data_source_id} config={config} />
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
    const { dataSource, fetchDataSourceEnvVars, setDataSourceEnvVars } = config;

    const {
        copiedField,
        copyToClipboard,
        getFullDataSourceJson,
        formatDate,
        formatTimeFromSeconds,
        formatJson,
    } = useDataSourceUtils();

    return (
        <>
            <DataSourceHeader
                dataSource={dataSource}
                copiedField={copiedField}
                onCopyToClipboard={copyToClipboard}
                onGetFullDataSourceJson={getFullDataSourceJson}
            />

            <Separator />

            {/* Main content */}
            <Tabs defaultValue="general" className="w-full">
                <TabsList className="mb-4">
                    <TabsTrigger value="general">General</TabsTrigger>
                    <TabsTrigger value="source">Source</TabsTrigger>
                    <TabsTrigger value="caching">Caching</TabsTrigger>
                </TabsList>

                <TabsContent value="general">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <DataSourceSummaryCard
                            dataSource={dataSource}
                            formatDate={formatDate}
                            formatJson={formatJson}
                        />

                        <EditableVariablesCard
                            dataSource={dataSource}
                            projectId={config.projectId}
                            fetchDataSourceEnvVars={fetchDataSourceEnvVars}
                            setDataSourceEnvVars={setDataSourceEnvVars}
                        />
                    </div>
                </TabsContent>

                <TabsContent value="source">
                    <div className="grid gap-4">
                        <SourceConfigurationCard dataSource={dataSource} formatJson={formatJson} />

                        <RetryPolicyCard dataSource={dataSource} />
                    </div>
                </TabsContent>

                <TabsContent value="caching">
                    <CachingConfigurationCard
                        dataSource={dataSource}
                        formatTimeFromSeconds={formatTimeFromSeconds}
                    />
                </TabsContent>
            </Tabs>
        </>
    );
}
