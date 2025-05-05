import { DataSource } from "@vulkan-server/DataSource";
import { fetchDataSource } from "@/lib/api";

import DataSourcePage from "./components";

export default async function Page(props) {
    const params = await props.params;

    const dataSource: DataSource = await fetchDataSource(params.data_source_id).catch((error) => {
        console.error(error);
        return null;
    });
    return <DataSourcePage dataSource={dataSource} />;
}
