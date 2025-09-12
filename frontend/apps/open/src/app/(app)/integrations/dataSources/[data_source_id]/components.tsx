"use client";

import { DataSourceDetailPage } from "@vulkanlabs/base";
import type { DataSource } from "@vulkanlabs/client-open";

import { fetchDataSourceEnvVars, setDataSourceEnvVars } from "@/lib/api";
import DataSourceUsageAnalytics from "./usage-analytics";

export default function DataSourcePage({ dataSource }: { dataSource: DataSource }) {
    return (
        <DataSourceDetailPage
            config={{
                dataSource,
                fetchDataSourceEnvVars,
                setDataSourceEnvVars,
                UsageAnalyticsComponent: DataSourceUsageAnalytics,
            }}
        />
    );
}
