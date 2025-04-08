import { stackServerApp } from "@/stack";

import { DataSource } from "@vulkan-server/DataSource";
import { fetchDataSource } from "@/lib/api";

import DataSourcePage from "./components";

export default async function Page(props) {
    const params = await props.params;
    const user = await stackServerApp.getUser();
    const dataSource: DataSource = await fetchDataSource(user, params.data_source_id).catch(
        (error) => {
            console.error(error);
            return [];
        },
    );
    return <DataSourcePage dataSource={dataSource} />;
}
