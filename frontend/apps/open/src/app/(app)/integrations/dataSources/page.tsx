import { fetchDataSources } from "@/lib/api";
import { SharedPageTemplate } from "@vulkanlabs/base";
import DataSourcesTable from "./data-sources-table";

export const dynamic = "force-dynamic";

export default async function Page() {
    return (
        <SharedPageTemplate 
            config={{
                title: "Data Sources",
                fetchData: fetchDataSources,
                TableComponent: DataSourcesTable,
                requiresProject: false,
                useSeparator: true,
                errorFallback: []
            }}
        />
    );
}
