import { stackServerApp } from "@/stack";

import { fetchDataSource } from "@/lib/api";
import { DataSource } from "../types";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const dataSource: DataSource = await fetchDataSource(user, params.data_source_id).catch(
        (error) => {
            console.error(error);
            return [];
        },
    );
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
                <p>{dataSource.retry?.status_forcelist ? dataSource.retry.status_forcelist.join(", ") : "null"}</p>
            </div>

        </div>
    );
}

function ParamsTable({ params }) {
    return (
        <table className="w-[40rem] divide-y divide-gray-200 border-collapse border-2">
            <thead>
                <tr>
                    <TableHeader>Key</TableHeader>
                    <TableHeader>Value</TableHeader>
                </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
                {params ? (
                    Object.entries(params).map(([key, value]) => (
                        <tr key={key}>
                            <TableCell>{key}</TableCell>
                            <TableCell>{value}</TableCell>
                        </tr>
                    ))
                ) : (
                    <tr>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                    </tr>
                )}
            </tbody>
        </table>
    );
}

function TableHeader({ children }) {
    return (
        <th className="xl:text-xs xl:px-4 xl:py-2 2xl:px-6 2xl:py-4 2xl:text-sm text-left border-r-2 font-medium text-gray-500 uppercase tracking-wider sticky top-0">
            {children}
        </th>
    );
}

function TableCell({ children }) {
    return (
        <td className="xl:text-xs xl:px-4 xl:py-2 2xl:px-6 2xl:py-4 2xl:text-sm border-r-2 whitespace-normal text-gray-500">
            {children}
        </td>
    );
}
