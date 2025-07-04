"use client";

import { ColumnDef } from "@tanstack/react-table";
import { DataTable, DetailsButton, ShortenedID } from "@vulkan/base";
import { parseDate } from "@/lib/utils";

const componentVersionColumns: ColumnDef<any>[] = [
    {
        header: "",
        accessorKey: "link",
        cell: ({ row }) => {
            const component_id = row.original["component_id"];
            const component_version_id = row.getValue("component_version_id");
            return (
                <DetailsButton
                    href={`/components/${component_id}/versions/${component_version_id}/workflow`}
                />
            );
        },
    },
    {
        header: "ID",
        accessorKey: "component_version_id",
        cell: ({ row }) => <ShortenedID id={row.getValue("component_version_id")} />,
    },
    {
        header: "Tag",
        accessorKey: "alias",
    },
    {
        header: "Input Schema",
        accessorKey: "input_schema",
    },
    {
        header: "Instance Params Schema",
        accessorKey: "instance_params_schema",
    },
    {
        header: "Created At",
        accessorKey: "created_at",
        cell: ({ row }) => parseDate(row.getValue("created_at")),
    },
];

export function ComponentVersionsTable({ versions }: { versions: any[] }) {
    return (
        <DataTable
            columns={componentVersionColumns}
            data={versions}
            emptyMessage="No versions found"
            className=""
        />
    );
}
