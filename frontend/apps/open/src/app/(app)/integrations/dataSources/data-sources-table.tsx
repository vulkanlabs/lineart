import { SharedDataSourcesTable, SharedCreateDataSourceDialog } from "@vulkanlabs/base";
import { DataSource } from "@vulkanlabs/client-open";
import { deleteDataSourceClient, createDataSourceClient } from "@/lib/api-client";

export default function DataSourcesTable({ dataSources }: { dataSources: DataSource[] }) {
    return (
        <SharedDataSourcesTable
            dataSources={dataSources}
            config={{
                deleteDataSource: deleteDataSourceClient,
                CreateDataSourceDialog: (
                    <SharedCreateDataSourceDialog
                        config={{
                            createDataSource: createDataSourceClient,
                        }}
                    />
                ),
            }}
        />
    );
}
