"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ShortenedID } from "@/components/shortened-id";

export default function DataSourcesPage({ dataSources }: { dataSources: any[] }) {
    const router = useRouter();
    console.log(dataSources);

    return (
        <div>
            <Button onClick={() => router.refresh()}>Refresh</Button>
            {dataSources.length > 0 ? <DataSourcesTable dataSources={dataSources} /> : <EmptyDataSourcesTable />}
        </div>
    );
}

export function DataSourcesTable({ dataSources }) {
    const router = useRouter();

    return (
        <Table>
            <TableCaption>Your data sources.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Created At</TableHead>
                    <TableHead>Last Updated At</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {dataSources.map((source) => (
                    <TableRow
                        key={source.data_source_id}
                        className="cursor-pointer"
                        onClick={() => router.push(`/integrations/dataSources/${source.data_source_id}`)}
                    >
                        <TableCell><ShortenedID id={source.data_source_id} /></TableCell>
                        <TableCell>{source.name}</TableCell>
                        <TableCell>
                            {source.description?.length > 0 ? source.description : "-"}
                        </TableCell>
                        <TableCell>{source.created_at}</TableCell>
                        <TableCell>{source.last_updated_at}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

function EmptyDataSourcesTable() {
    return (
        <div>
            <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed shadow-sm">
                <div className="flex flex-col items-center gap-1 text-center">
                    <h3 className="text-2xl font-bold tracking-tight">You don't have any data sources yet.</h3>
                    <p className="text-sm text-muted-foreground">
                        Create a data source to start using it in your workflows.
                    </p>
                </div>
            </div>
        </div>
    );
}
