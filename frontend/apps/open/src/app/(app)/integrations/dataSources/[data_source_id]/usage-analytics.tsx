// Local imports
import { DataSourceUsageAnalytics as SharedDataSourceUsageAnalytics } from "@vulkanlabs/base";
import {
    fetchDataSourceCacheStatsClient,
    fetchDataSourceMetricsClient,
    fetchDataSourceUsageClient,
} from "@/lib/api-client";

export default function DataSourceUsageAnalytics({ dataSourceId }: { dataSourceId: string }) {
    return (
        <SharedDataSourceUsageAnalytics
            dataSourceId={dataSourceId}
            config={{
                fetchUsage: async (id, from, to) => {
                    const data = await fetchDataSourceUsageClient(id, from, to);
                    return { requests_by_date: data.requests_by_date };
                },
                fetchMetrics: async (id, from, to) => {
                    const data = await fetchDataSourceMetricsClient(id, from, to);
                    return {
                        avg_response_time_by_date: data.avg_response_time_by_date,
                        error_rate_by_date: data.error_rate_by_date,
                    };
                },
                fetchCacheStats: async (id, from, to) => {
                    const data = await fetchDataSourceCacheStatsClient(id, from, to);
                    return { cache_hit_ratio_by_date: data.cache_hit_ratio_by_date };
                },
            }}
        />
    );
}
