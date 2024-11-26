"use client";
import Link from "next/link";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { RotateCw, ArrowLeft } from "lucide-react";
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

export function BacktestDetailsPage({ policyVersionId, backtest }) {
    return (
        <div className="flex flex-col py-4 px-8 gap-8">
            <Link href={`/policyVersions/${policyVersionId}/backtests`}>
                <button className="flex flex-row gap-2 bg-white text-black hover:text-gray-700 text-lg font-bold">
                    <ArrowLeft />
                    Back
                </button>
            </Link>
            <BackfillsTableComponent backfills={backtest.backfills} />
        </div>
    );  
}

function BackfillsTableComponent({ backfills }) {
    const router = useRouter();

    return (
        <div>
            <div className="flex justify-between items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Backfills</h1>
                <div className="flex gap-4">
                    <Button onClick={() => router.refresh()}>
                        <RotateCw className="mr-2" />
                        Refresh
                    </Button>
                </div>
            </div>
            <div className="max-h-[30vh] overflow-scroll">
                <BackfillsTable backfills={backfills} />
            </div>
        </div>
    );
}

function BackfillsTable({ backfills }) {
    return (
        <Table>
            <TableCaption>Backfill jobs.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Config Variables</TableHead>
                    <TableHead>Status</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {backfills.map((backfill) => (
                    <TableRow key={backfill.backfill_id}>
                        <TableCell>
                            <ShortenedID id={backfill.backfill_id} />
                        </TableCell>
                        <TableCell>{JSON.stringify(backfill.config_variables)}</TableCell>
                        <TableCell>{backfill.status}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
