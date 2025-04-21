"use client";
import Link from "next/link";
import React from "react";

import { Button } from "@/components/ui/button";
import { ShortenedID } from "@/components/shortened-id";
import { RefreshButton } from "@/components/refresh-button";
import { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/data-table";
import { DetailsButton } from "@/components/details-button";

import { Backtest } from "@vulkan-server/Backtest";
import { UploadedFile } from "@vulkan-server/UploadedFile";

import { parseDate } from "@/lib/utils";

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

const BacktestColumns: ColumnDef<Backtest>[] = [
    {
        accessorKey: "link",
        header: "",
        cell: ({ row }) => <DetailsButton href={`backtests/${row.getValue("backtest_id")}`} />,
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
