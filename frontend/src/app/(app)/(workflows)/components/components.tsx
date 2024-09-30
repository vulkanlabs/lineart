"use client";

import { useRouter } from "next/navigation";

import { EmptyAssetTable } from "@/components/empty-asset-table";
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

export default function ComponentPageContent({ components }) {
    return (
        <div>
            {components.length > 0 ? (
                <ComponentsTable components={components} />
            ) : (
                <EmptyAssetTable
                    title="You don't have any components yet."
                    description="Create a component to start using it in your workflows."
                />
            )}
        </div>
    );
}

function ComponentsTable({ components }) {
    const router = useRouter();

    return (
        <Table>
            <TableCaption>List of your components.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {components.map((entry) => (
                    <TableRow
                        key={entry.component_id}
                        className="cursor-pointer"
                        onClick={() => router.push(`/components/${entry.component_id}`)}
                    >
                        <TableCell>{entry.component_id}</TableCell>
                        <TableCell>{entry.name}</TableCell>
                        <TableCell> - </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
