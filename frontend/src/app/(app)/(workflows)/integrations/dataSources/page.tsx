import { stackServerApp } from "@/stack";

import DataSourcesPage from "./components";
import { fetchDataSources } from "@/lib/api";

export default async function Page() {
    const user = await stackServerApp.getUser();
    const dataSources = await fetchDataSources(user).catch((error) => {
        console.error(error);
        return [];
    });
    return (
        <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div className="flex items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Data Sources</h1>
            </div>
            <DataSourcesPage dataSources={dataSources} />
        </main>
    );
}
