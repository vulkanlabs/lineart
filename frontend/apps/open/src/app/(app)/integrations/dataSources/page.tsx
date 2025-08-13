import { fetchDataSources } from "@/lib/api";
import { Separator } from "@vulkanlabs/base/ui";
import DataSourcesTable from "./data-sources-table";

export const dynamic = "force-dynamic";

export default async function Page() {
    const dataSources = await fetchDataSources().catch((error) => {
        console.error(error);
        return [];
    });
    return (
        <div className="flex flex-1 flex-col gap-6 p-4 lg:gap-6 lg:p-6">
            <div className="flex flex-col gap-4">
                <h1 className="text-lg font-semibold md:text-2xl">Data Sources</h1>
                <Separator />
            </div>
            <DataSourcesTable dataSources={dataSources} />
        </div>
    );
}
