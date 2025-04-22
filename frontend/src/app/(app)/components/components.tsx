"use client";

import { DetailsButton } from "@/components/details-button";
import { useRouter } from "next/navigation";

import { DataTable } from "@/components/data-table";
import { ShortenedID } from "@/components/shortened-id";
import { Button } from "@/components/ui/button";
import { ColumnDef } from "@tanstack/react-table";

export default function ComponentPageContent({ components }) {
    const router = useRouter();

    return (
        <div>
            <Button onClick={() => router.refresh()}>Refresh</Button>
            <div className="mt-4">
                <DataTable
                    columns={componentsTableColumns}
                    data={components}
                    emptyMessage="Create a component to start using it in your workflows."
                />
            </div>
        </div>
    );
}

const componentsTableColumns: ColumnDef<any>[] = [
    {
        accessorKey: "link",
        header: "",
        cell: ({ row }) => <DetailsButton href={`components/${row.getValue("component_id")}`} />,
    },
    {
        accessorKey: "component_id",
        header: "ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("component_id")} />,
    },
    {
        accessorKey: "name",
        header: "Name",
    },
];
