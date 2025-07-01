"use client";

import React, { useState, useEffect } from "react";
import { subDays, formatDistanceStrict } from "date-fns";
import { useRouter } from "next/navigation";
import { ArrowUpDown, RefreshCcw } from "lucide-react";
import { Badge } from "@/components/ui/badge";

import { ColumnDef } from "@tanstack/react-table";
import { Button } from "@/components/ui/button";

import { ShortenedID } from "@/components/shortened-id";
import { DetailsButton } from "@/components/details-button";
import { DatePickerWithRange } from "@/components/charts/date-picker";
import { ResourceTable } from "@/components/resource-table";
import { parseDate } from "../../lib/utils";

import { Run } from "@vulkan-server/Run";
import { DateRange } from "react-day-picker";

type RunsLoader = ({
    resourceId,
    dateRange,
}: {
    resourceId: string;
    dateRange: DateRange;
}) => Promise<{
    runs: Run[] | null;
}>;

export function RunsPage({ resourceId, fetchRuns }: { resourceId: string; fetchRuns: RunsLoader }) {
    const [dateRange, setDateRange] = useState<DateRange>({
        from: subDays(new Date(), 7),
        to: new Date(),
    });
    const [runs, setRuns] = useState<Run[]>([]);
    const router = useRouter();

    useEffect(() => {
        if (!dateRange || !dateRange.from || !dateRange.to) {
            return;
        }

        fetchRuns({ resourceId, dateRange })
            .then((data) => {
                setRuns(data.runs);
            })
            .catch((error) => {
                console.error(error);
            });
    }, [dateRange]);

    return (
        <div className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <h1 className="text-lg font-semibold md:text-2xl">Runs</h1>
            <div className="flex flex-row gap-2 items-center">
                <DatePickerWithRange date={dateRange} setDate={setDateRange} />
                <Button variant="outline" onClick={() => router.refresh()}>
                    <RefreshCcw className="h-4 w-4" />
                </Button>
            </div>
            <div className="flex flex-col gap-4">
                <ResourceTable columns={RunsTableColumns} data={runs} disableFilters />
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
        accessorKey: "run_group_id",
        header: "Run Group ID",
        cell: ({ row }) => {
            const run_group_id: string = row.getValue("run_group_id");
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
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    className="p-0"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                >
                    <span className="mr-2">Created At</span>
                    <ArrowUpDown className="w-5 h-5" />
                </Button>
            );
        },
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
    if (value == "SUCCESS") {
        return <Badge className="bg-green-100 text-green-800 border-green-300">{value}</Badge>;
    }

    if (value == "FAILURE") {
        return (
            <Badge variant="outline" className="bg-red-100 text-red-800 border-red-300">
                {value}
            </Badge>
        );
    }

    return <Badge variant="outline">{value}</Badge>;
}
