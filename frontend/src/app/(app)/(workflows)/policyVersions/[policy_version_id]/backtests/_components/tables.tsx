"use client";
import Link from "next/link";
import React from "react";
import { usePathname, useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { ShortenedID } from "@/components/shortened-id";
import { RefreshButton } from "@/components/refresh-button";
import { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/data-table";
import { LucideMousePointerClick } from "lucide-react";

export function BacktestsTableComponent({ policyVersionId, backtests }) {
    const launcherRef = `/policyVersions/${policyVersionId}/backtests/backtestLauncher`;

    return (
        <div>
            <div className="flex justify-between items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Backtests</h1>
                <div className="flex gap-4">
                    <Link href={launcherRef}>
                        <Button className="bg-blue-600 hover:bg-blue-500">Create Backtest</Button>
                    </Link>
                    <RefreshButton />
                </div>
            </div>
            <div className="max-h-[30vh] overflow-scroll mt-4">
                <DataTable columns={BacktestColumns} data={backtests} />
            </div>
        </div>
    );
}

type Backtest = {
    backtest_id: string;
    input_file_id: string;
    status: string;
    calculate_metrics: boolean;
    created_at: string;
};

const BacktestColumns: ColumnDef<Backtest>[] = [
    {
        accessorKey: "link",
        header: "",
        cell: ({ row }) => (
            <Button variant="ghost" className="h-8 w-8 p-0">
                <Link href={`backtests/${row.getValue("backtest_id")}`}>
                    <LucideMousePointerClick />
                </Link>
            </Button>
        ),
    },
    {
        accessorKey: "backtest_id",
        header: "ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("backtest_id")} />,
    },
    {
        accessorKey: "input_file_id",
        header: "Input File ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("input_file_id")} />,
    },
    {
        accessorKey: "status",
        header: "Status",
    },
    {
        accessorKey: "calculate_metrics",
        header: () => <div className="text-right">Metrics Enabled</div>,
        cell: ({ row }) => {
            const status = row.getValue("calculate_metrics") ? "Yes" : "No";
            return <div className="text-right">{status}</div>;
        },
    },
    {
        accessorKey: "created_at",
        header: "Created At",
        cell: ({ row }) => parseDate(row.getValue("created_at")),
    },
];

function parseDate(date: string) {
    return new Date(date).toLocaleString();
}

export function UploadedFilesTableComponent({ policyVersionId, uploadedFiles }) {
    const uploaderRef = `/policyVersions/${policyVersionId}/backtests/fileUploader`;

    return (
        <div>
            <div className="flex justify-between items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Uploaded Files</h1>
                <div className="flex gap-4">
                    <Link href={uploaderRef}>
                        <Button className="bg-blue-600 hover:bg-blue-500">Upload File</Button>
                    </Link>
                    <RefreshButton />
                </div>
            </div>
            <div className="max-h-[30vh] overflow-scroll mt-4">
                <DataTable columns={UploadedFilesColumns} data={uploadedFiles} />
            </div>
        </div>
    );
}

type UploadedFile = {
    uploaded_file_id: string;
    file_schema: Record<string, any>;
    created_at: string;
};

const UploadedFilesColumns: ColumnDef<UploadedFile>[] = [
    {
        accessorKey: "uploaded_file_id",
        header: "ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("uploaded_file_id")} />,
    },
    {
        accessorKey: "file_schema",
        header: "File Schema",
        cell: ({ row }) => JSON.stringify(row.getValue("file_schema"), null, 2),
    },
    {
        accessorKey: "created_at",
        header: "Created At",
        cell: ({ row }) => parseDate(row.getValue("created_at")),
    },
];
