"use client";

import { DataTable } from "@/components/data-table";
import { DetailsButton } from "@/components/details-button";
import { ShortenedID } from "@/components/shortened-id";
import { parseDate } from "@/lib/utils";
import { ColumnDef } from "@tanstack/react-table";
import { ComponentVersion } from "@vulkan-server/ComponentVersion";

const componentVersionColumns: ColumnDef<ComponentVersion>[] = [
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

export function ComponentVersionsTable({ versions }) {
    return <DataTable columns={componentVersionColumns} data={versions} />;
}
