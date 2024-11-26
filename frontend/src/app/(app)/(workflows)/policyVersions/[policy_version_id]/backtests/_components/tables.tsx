"use client";
import Link from "next/link";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { RotateCw } from "lucide-react";
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

export function BacktestsTableComponent({ backtests }) {
    const router = useRouter();

    return (
        <div>
            <div className="flex justify-between items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Backtests</h1>
                <div className="flex gap-4">
                    <Link href={`${window.location.pathname}/backtestLauncher`}>
                        <Button className="bg-blue-600 hover:bg-blue-500">Create Backtest</Button>
                    </Link>
                    <Button onClick={() => router.refresh()}>
                        <RotateCw className="mr-2" />
                        Refresh
                    </Button>
                </div>
            </div>
            <div className="max-h-[30vh] overflow-scroll">
                <BacktestsTable backtests={backtests} />
            </div>
        </div>
    );
}

function BacktestsTable({ backtests }) {
    const router = useRouter();

    function parseDate(date: string) {
        return new Date(date).toLocaleString();
    }

    return (
        <Table>
            <TableCaption>Your Backtests.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Input File ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created At</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {backtests.map((backtest) => (
                    <TableRow
                        key={backtest.backtest_id}
                        className="cursor-pointer"
                        onClick={() =>
                            router.push(`${window.location.pathname}/${backtest.backtest_id}`)
                        }
                    >
                        <TableCell>
                            <ShortenedID id={backtest.backtest_id} />
                        </TableCell>
                        <TableCell>
                            <ShortenedID id={backtest.input_file_id} />
                        </TableCell>
                        <TableCell>{backtest.status}</TableCell>
                        <TableCell>{parseDate(backtest.created_at)}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

export function UploadedFilesTableComponent({ uploadedFiles }) {
    const router = useRouter();

    return (
        <div>
            <div className="flex justify-between items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Uploaded Files</h1>
                <div className="flex gap-4">
                    <Link href={`${window.location.pathname}/backtests/fileUploader`}>
                        <Button className="bg-blue-600 hover:bg-blue-500">Upload File</Button>
                    </Link>
                    <Button onClick={() => router.refresh()}>
                        <RotateCw className="mr-2" />
                        Refresh
                    </Button>
                </div>
            </div>
            <div className="max-h-[30vh] overflow-scroll">
                <UploadedFilesTable uploadedFiles={uploadedFiles} />
            </div>
        </div>
    );
}

function UploadedFilesTable({ uploadedFiles }) {
    function parseDate(date: string) {
        return new Date(date).toLocaleString();
    }

    return (
        <Table>
            <TableCaption>Your Uploaded Files.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>File Schema</TableHead>
                    <TableHead>Created At</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {uploadedFiles.map((file) => (
                    <TableRow key={file.uploaded_file_id}>
                        <TableCell>
                            <ShortenedID id={file.uploaded_file_id} />
                        </TableCell>
                        <TableCell>{JSON.stringify(file.file_schema)}</TableCell>
                        <TableCell>{parseDate(file.created_at)}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
