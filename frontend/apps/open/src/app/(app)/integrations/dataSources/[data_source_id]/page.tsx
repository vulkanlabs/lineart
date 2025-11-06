// Vulkan packages
import type { DataSource } from "@vulkanlabs/client-open";
import { DataSourceDetailPage } from "@vulkanlabs/base/components/data-sources";
import { revalidatePath } from "next/cache";

// Local imports
import {
    fetchDataSource,
    fetchDataSourceEnvVars,
    fetchDataSourceCredentials,
    fetchDataSourceCacheStats,
    fetchDataSourceMetrics,
    fetchDataSourceUsage,
    setDataSourceEnvVars,
    setDataSourceCredentials,
    updateDataSource,
    testDataSource,
    publishDataSource,
} from "@/lib/api";

export default async function Page(props: { params: Promise<{ data_source_id: string }> }) {
    const params = await props.params;
    const { data_source_id } = params;
    const dataSource: DataSource | null = await fetchDataSource(data_source_id).catch((error) => {
        console.error(error);
        return null;
    });

    if (!dataSource) {
        return (
            <div className="flex flex-col items-center justify-center h-screen p-4 text-center">
                <h1 className="mb-4 text-2xl font-bold">Data Source Not Found</h1>
                <p className="mb-2 text-lg">
                    Data source with ID <code>{data_source_id}</code> not found.
                </p>
                <p className="mb-4 text-lg">Please check the ID and try again.</p>
            </div>
        );
    }

    const withRevalidation = <T,>(fn: (...args: any[]) => Promise<T>) => {
        return async (...args: any[]): Promise<T> => {
            "use server";
            const result = await fn(...args);
            revalidatePath(`/integrations/dataSources/${data_source_id}`);
            return result;
        };
    };

    return (
        <DataSourceDetailPage
            config={{
                dataSource,
                fetchDataSource,
                updateDataSource: withRevalidation(updateDataSource),
                fetchDataSourceEnvVars,
                setDataSourceEnvVars,
                fetchDataSourceCredentials,
                setDataSourceCredentials,
                fetchUsage: fetchDataSourceUsage,
                fetchMetrics: fetchDataSourceMetrics,
                fetchCacheStats: fetchDataSourceCacheStats,
                testDataSource,
                publishDataSource: withRevalidation(publishDataSource),
            }}
        />
    );
}
