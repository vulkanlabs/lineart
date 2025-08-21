import { Suspense } from "react";
import { SharedDataSourcesTable } from "@vulkanlabs/base";
import { DataSource } from "@vulkanlabs/client-open";
import { deleteDataSourceAction } from "./actions";
import { CreateDataSourceDialog } from "../../../../components/data-sources/create-dialog";

export default function DataSourcesTable({ dataSources }: { dataSources: DataSource[] }) {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <SharedDataSourcesTable
                dataSources={dataSources}
                config={{
                    deleteDataSource: deleteDataSourceAction,
                    CreateDataSourceDialog: <CreateDataSourceDialog />,
                }}
            />
        </Suspense>
    );
}
