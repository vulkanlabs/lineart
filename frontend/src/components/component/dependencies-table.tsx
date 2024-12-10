"use client";
import { ShortenedID } from "@/components/shortened-id";
import Link from "next/link";

import { DataTable } from "@/components/data-table";
import { ColumnDef } from "@tanstack/react-table";
import { ComponentVersionDependencyExpanded } from "@vulkan-server/ComponentVersionDependencyExpanded";
import { LinkIcon } from "lucide-react";

const ComponentDependenciesTableColumns: ColumnDef<ComponentVersionDependencyExpanded>[] = [
    {
        accessorKey: "component_version_id",
        header: "Component ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("component_version_id")} />,
    },
    {
        accessorKey: "component_version_alias",
        header: "Component Version",
    },
    {
        accessorKey: "policy_id",
        header: "Policy ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("policy_id")} />,
    },
    {
        accessorKey: "policy_name",
        header: "Policy Name",
    },
    {
        accessorKey: "policy_version_id",
        header: "Policy Version",
        cell: ({ row }) => <ShortenedID id={row.getValue("policy_version_id")} />,
    },
    {
        accessorKey: "policy_version_alias",
        header: "Version Tag",
    },
];

export function ComponentVersionDependenciesTable({
    entries,
}: {
    entries: ComponentVersionDependencyExpanded[];
}) {
    return <DataTable columns={ComponentDependenciesTableColumns} data={entries} />;
}

const PolicyDependenciesTableColumns: ColumnDef<ComponentVersionDependencyExpanded>[] = [
    {
        accessorKey: "link",
        header: "",
        cell: ({ row }) => (
            <Link href={`/components/${row.getValue("component_id")}`}>
                <LinkIcon />
            </Link>
        ),
    },
    {
        accessorKey: "component_name",
        header: "Component Name",
    },
    {
        accessorKey: "component_version_alias",
        header: "Component Version",
    },
    {
        accessorKey: "component_id",
        header: "Component ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("component_id")} />,
    },
    {
        accessorKey: "component_version_id",
        header: "Component ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("component_version_id")} />,
    },
];

export function PolicyVersionComponentDependenciesTable({
    entries,
}: {
    entries: ComponentVersionDependencyExpanded[];
}) {
    if (!entries || entries.length === 0) {
        return <EmptyDependenciesTable />;
    }

    return <DataTable columns={PolicyDependenciesTableColumns} data={entries} />;
}

function EmptyDependenciesTable() {
    return (
        <div className="flex justify-center items-center h-32 text-gray-500">
            No dependencies found.
        </div>
    );
}
