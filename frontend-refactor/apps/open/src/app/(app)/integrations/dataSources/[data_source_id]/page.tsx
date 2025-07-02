import { DataSource } from "@vulkan/client-open/models/DataSource";
import { fetchDataSource } from "@/lib/api";

import DataSourcePage from "./components";

export default async function Page(props) {
    const params = await props.params;
    const dataSource: DataSource = await fetchDataSource(params.data_source_id).catch((error) => {
        console.error(error);
        return null;
    });

    if (!dataSource) {
        return (
            <div className="flex flex-col items-center justify-center h-screen p-4 text-center">
                <h1 className="mb-4 text-2xl font-bold">Data Source Not Found</h1>
                <p className="mb-2 text-lg">
                    Data source with ID <code>{params.data_source_id}</code> not found.
                </p>
                <p className="mb-4 text-lg">Please check the ID and try again.</p>
            </div>
        );
    }

    return <DataSourcePage dataSource={dataSource} />;
}
