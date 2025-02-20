"use client";
import { formatDistanceStrict } from "date-fns";

import { ColumnDef } from "@tanstack/react-table";
import { Run } from "@vulkan-server/Run";

import { DataTable } from "@/components/data-table";
import { ShortenedID } from "@/components/shortened-id";
import { DetailsButton } from "@/components/details-button";
import { RefreshButton } from "@/components/refresh-button";
import { parseDate } from "@/lib/utils";

export function RunsPage({ runs }: { runs: Run[] }) {
    return (
        <div className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <h1 className="text-lg font-semibold md:text-2xl">Runs</h1>
            <div className="flex flex-col gap-4">
                <div>
                    <RefreshButton />
                </div>
                <RunsTableComponent runs={runs} />
            </div>
        </div>
    );
}

function RunsTableComponent({ runs }: { runs: Run[] }) {
    return (
        <DataTable
            columns={RunsTableColumns}
            data={runs}
            emptyMessage="You don't have any runs yet."
            className="max-h-[67vh]"
        />
    );
}

const RunsTableColumns: ColumnDef<Run>[] = [
    {
        accessorKey: "link",
        header: "",
        cell: ({ row }) => <DetailsButton href={`runs/${row.getValue("run_id")}`} />,
    },
    {
        accessorKey: "run_id",
        header: "ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("run_id")} />,
    },
    {
        accessorKey: "policy_version_id",
        header: "Version ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("policy_version_id")} />,
    },
    {
        accessorKey: "run_group_id",
        header: "Run Group ID",
        cell: ({ row }) => {
            const run_group_id : string = row.getValue("run_group_id");
            return run_group_id == null ? "-" : <ShortenedID id={run_group_id} />;
        },
    },
    {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <RunStatus value={row.getValue("status")} />,
    },
    {
        accessorKey: "result",
        header: "Result",
        cell: ({ row }) => {
            const result = row.getValue("result");
            return result == null || result == "" ? "-" : result;
        },
    },
    {
        accessorKey: "created_at",
        header: "Created At",
        cell: ({ row }) => parseDate(row.getValue("created_at")),
    },
    {
        accessorKey: "duration",
        header: "Duration",
        cell: ({ row }) => {
            return formatDistanceStrict(row.original.last_updated_at, row.original.created_at);
        },
    },
];

function RunStatus({ value }) {
    const getColor = (status) => {
        switch (status) {
            case "SUCCESS":
                return "bg-green-200";
            case "FAILURE":
                return "bg-red-200";
            default:
                return "bg-gray-200";
        }
    };

    return <p className={`w-fit p-[0.3em] rounded-lg ${getColor(value)}`}>{value}</p>;
}
