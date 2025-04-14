import { fetchDataSource } from "@/lib/api";
import { DataSource } from "../types";
import { ColumnDef } from "@tanstack/react-table";
import { ConfigurationVariablesBase } from "@vulkan-server/ConfigurationVariablesBase";
import { DataTable } from "@/components/data-table";

export default async function Page(props) {
    const params = await props.params;
    const dataSource: DataSource = await fetchDataSource(params.data_source_id).catch((error) => {
        console.error(error);
        return [];
    });
    return (
        <div className="m-10 flex flex-col gap-6">
            <div className="flex flex-row gap-4">
                <h1 className="font-semibold text-stone-700">Name:</h1>
                <p>{dataSource.name}</p>
            </div>
            <div className="flex flex-row gap-4">
                <h1 className="font-semibold text-stone-700">Description:</h1>
                <p>{dataSource.description ? dataSource.description : "null"}</p>
            </div>

            <h1 className="mt-5 text-lg font-bold text-stone-700">Request</h1>
            <div className="flex flex-row gap-4">
                <h1 className="font-semibold text-stone-700">URL:</h1>
                <p>{dataSource.request.url}</p>
            </div>
            <div className="flex flex-row gap-4">
                <h1 className="font-semibold text-stone-700">Method:</h1>
                <p>{dataSource.request.method}</p>
            </div>
            <h1 className="font-semibold text-stone-700">Headers:</h1>
            <ParamsTable params={dataSource.request.headers} />
            <h1 className="font-semibold text-stone-700">Params:</h1>
            <ParamsTable params={dataSource.request.params} />
            <h1 className="font-semibold text-stone-700">Body Schema:</h1>
            <ParamsTable params={dataSource.request.body_schema} />

            <h1 className="mt-5 text-lg font-bold text-stone-700">Caching</h1>
            <div className="flex flex-row gap-4">
                <h1 className="font-semibold text-stone-700">Enabled:</h1>
                <p>{dataSource.caching.enabled.toString()}</p>
            </div>
            <div className="flex flex-row gap-4">
                <h1 className="font-semibold text-stone-700">TTL:</h1>
                <p>{JSON.stringify(dataSource.caching.ttl)}s</p>
            </div>

            <h1 className="mt-5 text-lg font-bold text-stone-700">Retry Policy</h1>
            <div className="flex flex-row gap-4">
                <h1 className="font-semibold text-stone-700">Max Retries:</h1>
                <p>{dataSource.retry?.max_retries}</p>
            </div>
            <div className="flex flex-row gap-4">
                <h1 className="font-semibold text-stone-700">Backoff Factor:</h1>
                <p>{dataSource.retry?.backoff_factor}</p>
            </div>
            <div className="flex flex-row gap-4">
                <h1 className="font-semibold text-stone-700">Status Forcelist:</h1>
                <p>
                    {dataSource.retry?.status_forcelist
                        ? dataSource.retry.status_forcelist.join(", ")
                        : "null"}
                </p>
            </div>
        </div>
    );
}

const paramsTableColumns: ColumnDef<ConfigurationVariablesBase>[] = [
    {
        accessorKey: "key",
        header: "Key",
        cell: ({ row }) => <p>{row.getValue("key") || "-"}</p>,
    },
    {
        accessorKey: "value",
        header: "Value",
        cell: ({ row }) => <p>{row.getValue("value") || "-"}</p>,
    },
];

function ParamsTable({ params }) {
    return <DataTable columns={paramsTableColumns} data={params} />;
}
