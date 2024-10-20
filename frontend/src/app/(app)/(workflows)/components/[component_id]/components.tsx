"use client";

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

export function ComponentVersionsTable({ versions }) {
    const router = useRouter();

    return (
        <Table>
            <TableCaption>Available versions.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Tag</TableHead>
                    <TableHead>Input Schema</TableHead>
                    <TableHead>Instance Params Schema</TableHead>
                    <TableHead>Created At</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {versions.map((entry) => (
                    <TableRow
                        key={entry.component_version_id}
                        className="cursor-pointer"
                        onClick={() =>
                            router.push(
                                `/components/${entry.component_id}/versions/${entry.component_version_id}/workflow`,
                            )
                        }
                    >
                        <TableCell>{entry.component_version_id}</TableCell>
                        <TableCell>{entry.alias}</TableCell>
                        <TableCell>{entry.input_schema}</TableCell>
                        <TableCell>{entry.instance_params_schema}</TableCell>
                        <TableCell>{entry.created_at}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
