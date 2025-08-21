import { SharedDataSourcesTable, SharedCreateDataSourceDialog } from "@vulkanlabs/base";
import { DataSource } from "@vulkanlabs/client-open";
import { deleteDataSourceAction, createDataSourceAction } from "./actions";

export default function DataSourcesTable({ dataSources }: { dataSources: DataSource[] }) {
    return (
        <SharedDataSourcesTable
            dataSources={dataSources}
            config={{
                deleteDataSource: deleteDataSourceAction,
                CreateDataSourceDialog: (
                    <SharedCreateDataSourceDialog
                        config={{
                            createDataSource: createDataSourceAction,
                        }}
                    />
                ),
            }}
        />
    );
}
