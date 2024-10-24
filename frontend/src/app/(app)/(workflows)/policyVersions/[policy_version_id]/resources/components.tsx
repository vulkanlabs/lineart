import React from "react";
import { LinkIcon } from "lucide-react";
import Link from "next/link";

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

export function ConfigVariablesTable({ variables }) {
    return (
        <Table>
            <TableCaption>Configuration variables for this Policy Version.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Created At</TableHead>
                    <TableHead>Last Updated At</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {variables.map((entry) => (
                    <TableRow key={entry.name}>
                        <TableCell>{entry.name}</TableCell>
                        <TableCell>{entry.value}</TableCell>
                        <TableCell>{entry.created_at}</TableCell>
                        <TableCell>{entry.last_updated_at}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

export function DataSourcesTable({ sources }) {
    function parseDate(date: string) {
        return new Date(date).toLocaleString();
    }

    return (
        <Table>
            <TableCaption>Data Sources for this Policy Version.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>Data Source Name</TableHead>
                    <TableHead>Data Source ID</TableHead>
                    <TableHead>Created At</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {sources.map((entry) => (
                    <TableRow key={entry.name}>
                        <TableCell>{entry.name}</TableCell>
                        <TableCell>
                            <ShortenedID id={entry.data_source_id} />
                        </TableCell>
                        <TableCell>{parseDate(entry.created_at)}</TableCell>
                        <TableCell>
                            <Link href={`/integrations/dataSources/${entry.data_source_id}`}>
                                <LinkIcon />
                            </Link>
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

export function EmptyVariablesTable() {
    return (
        <div>
            <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed shadow-sm">
                <div className="flex flex-col items-center gap-1 text-center">
                    <h3 className="text-2xl font-bold tracking-tight">
                        This policy version has no configurable variables.
                    </h3>
                </div>
            </div>
        </div>
    );
}
