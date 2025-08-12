// Local imports
import { DataSourcesTable as SharedDataSourcesTable } from "@vulkanlabs/base";
import { DataSource } from "@vulkanlabs/client-open";
import { deleteDataSource } from "@/lib/api";
import { CreateDataSourceDialog } from "../../../../components/data-sources/create-dialog";

export default function DataSourcesTable({ dataSources }: { dataSources: DataSource[] }) {
    return (
        <SharedDataSourcesTable
            dataSources={dataSources}
            config={{
                deleteDataSource: (id) => deleteDataSource(id),
                CreateDataSourceDialog: <CreateDataSourceDialog />,
            }}
        />
    );
}
