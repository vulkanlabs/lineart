"use client";
import { formatDistanceStrict } from "date-fns";

import { DataTable } from "@/components/data-table";
import { ShortenedID } from "@/components/shortened-id";
import { ColumnDef } from "@tanstack/react-table";
import { RefreshButton } from "../refresh-button";

import { DetailsButton } from "@/components/details-button";

import { Run } from "@vulkan-server/Run";

import { parseDate } from "@/lib/utils";

type RunsTableProps = {
    runs: Run[];
    policyVersionId?: string;
};

export function RunsTableComponent({ runs }: RunsTableProps) {
    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div className="flex justify-between items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Runs</h1>
                <RefreshButton />
            </div>
            <div className="mt-4 max-h-[75vh] overflow-scroll">
                <DataTable columns={RunsTableColumns} data={runs} />
            </div>
        </div>
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
