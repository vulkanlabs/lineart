// Local imports
import { DataSourceUsageAnalytics as SharedDataSourceUsageAnalytics } from "@vulkanlabs/base";
import {
    fetchDataSourceCacheStats,
    fetchDataSourceMetrics,
    fetchDataSourceUsage,
} from "@/lib/api";

export default function DataSourceUsageAnalytics({ dataSourceId }: { dataSourceId: string }) {
    return (
        <SharedDataSourceUsageAnalytics
            dataSourceId={dataSourceId}
            config={{
                fetchUsage: async (id: string, from: string, to: string) => {
                    const data = await fetchDataSourceUsage(id, new Date(from), new Date(to));
                    return { requests_by_date: (data as any).requests_by_date };
                },
                fetchMetrics: async (id: string, from: string, to: string) => {
                    const data = await fetchDataSourceMetrics(id, new Date(from), new Date(to));
                    return {
                        avg_response_time_by_date: (data as any).avg_response_time_by_date,
                        error_rate_by_date: (data as any).error_rate_by_date,
                    };
                },
                fetchCacheStats: async (id: string, from: string, to: string) => {
                    const data = await fetchDataSourceCacheStats(id, new Date(from), new Date(to));
                    return { cache_hit_ratio_by_date: (data as any).cache_hit_ratio_by_date };
                },
            }}
        />
    );
}
