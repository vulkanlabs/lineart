import React from "react";

import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

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

export function EmptyVariablesTable() {
    return (
        <div className="flex justify-center items-center h-32 text-gray-500">
            This policy version has no configurable variables.
        </div>
    );
}
