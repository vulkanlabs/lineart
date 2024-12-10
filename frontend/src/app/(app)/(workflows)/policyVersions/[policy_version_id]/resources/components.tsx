"use client";
import { LinkIcon } from "lucide-react";
import Link from "next/link";

import { DataTable } from "@/components/data-table";
import { ShortenedID } from "@/components/shortened-id";
import { parseDate } from "@/lib/utils";
import { ColumnDef } from "@tanstack/react-table";
import { ConfigurationVariables } from "@vulkan-server/ConfigurationVariables";
import { DataSource } from "@vulkan-server/DataSource";

const ConfigVariablesTableColumns: ColumnDef<ConfigurationVariables>[] = [
    {
        accessorKey: "name",
        header: "Name",
    },
    {
        accessorKey: "value",
        header: "Value",
    },
    {
        accessorKey: "created_at",
        header: "Created At",
        cell: ({ row }) => parseDate(row.getValue("created_at")),
    },
    {
        accessorKey: "last_updated_at",
        header: "Last Updated At",
        cell: ({ row }) => parseDate(row.getValue("last_updated_at")),
    },
];

export function ConfigVariablesTable({ variables }) {
    return <DataTable columns={ConfigVariablesTableColumns} data={variables} />;
}

const DataSourceTableColumns: ColumnDef<DataSource>[] = [
    {
        accessorKey: "link",
        header: "Link",
        cell: ({ row }) => (
            <Link href={`/integrations/dataSources/${row.getValue("data_source_id")}`}>
                <LinkIcon />
            </Link>
        ),
    },
    {
        accessorKey: "name",
        header: "Data Source Name",
    },
    {
        accessorKey: "data_source_id",
        header: "Data Source ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("data_source_id")} />,
    },
    {
        accessorKey: "created_at",
        header: "Created At",
        cell: ({ row }) => parseDate(row.getValue("created_at")),
    },
];

export function DataSourcesTable({ sources }) {
    return <DataTable columns={DataSourceTableColumns} data={sources} />;
}
