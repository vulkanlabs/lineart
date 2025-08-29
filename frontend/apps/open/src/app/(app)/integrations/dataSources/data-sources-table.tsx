import { SharedDataSourcesTable, SharedCreateDataSourceDialog } from "@vulkanlabs/base";
import { DataSource } from "@vulkanlabs/client-open";
import { deleteDataSource, createDataSource } from "@/lib/api";

export default function DataSourcesTable({ dataSources }: { dataSources: DataSource[] }) {
    return (
        <SharedDataSourcesTable
            dataSources={dataSources}
            config={{
                deleteDataSource: deleteDataSource,
                CreateDataSourceDialog: (
                    <SharedCreateDataSourceDialog
                        config={{
                            createDataSource: createDataSource,
                        }}
                    />
                ),
            }}
        />
    );
}
