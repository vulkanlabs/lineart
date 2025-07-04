"use client";

import { useRouter } from "next/navigation";
import { ColumnDef } from "@tanstack/react-table";

import { DetailsButton, DataTable, ShortenedID } from "@vulkan/base";
import { Button } from "@vulkan/base/ui";

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
