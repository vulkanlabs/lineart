"use client";

// React and Next.js
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

// External libraries
import { subDays, formatDistanceStrict } from "date-fns";
import { ArrowUpDown, RefreshCcw } from "lucide-react";
import { ColumnDef } from "@tanstack/react-table";
import { DateRange } from "react-day-picker";

// Vulkan packages
import { Badge, Button } from "@vulkanlabs/base/ui";
import { ShortenedID, DetailsButton, DatePickerWithRange, ResourceTable } from "@vulkanlabs/base";
import type { Run } from "@vulkanlabs/client-open";

// Local imports
import { parseDate } from "@/lib/utils";

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
                setRuns(data.runs || []);
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
            const lastUpdated = row.original.last_updated_at;
            const createdAt = row.original.created_at;

            if (!lastUpdated || !createdAt) {
                return "-";
            }

            try {
                return formatDistanceStrict(new Date(lastUpdated), new Date(createdAt));
            } catch (error) {
                return "-";
            }
        },
    },
];

function RunStatus({ value }: { value: string }) {
    if (value == "SUCCESS") {
        return (
            <Badge variant="default" className="bg-green-100 text-green-800 border-green-300">
                {value}
            </Badge>
        );
    }

    if (value == "FAILURE") {
        return (
            <Badge variant="outline" className="bg-red-100 text-red-800 border-red-300">
                {value}
            </Badge>
        );
    }

    return (
        <Badge variant="outline" className="">
            {value}
        </Badge>
    );
}
