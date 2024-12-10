"use client";

import { useRouter } from "next/navigation";

import { DataTable } from "@/components/data-table";
import { DetailsButton } from "@/components/details-button";
import { ShortenedID } from "@/components/shortened-id";
import { Button } from "@/components/ui/button";
import { parseDate } from "@/lib/utils";
import { ColumnDef } from "@tanstack/react-table";
import { DataSource } from "@vulkan-server/DataSource";

export default function DataSourcesPage({ dataSources }: { dataSources: DataSource[] }) {
    const router = useRouter();
    const emptyMessage = "Create a data source to start using it in your workflows.";

    return (
        <div>
            <Button onClick={() => router.refresh()}>Refresh</Button>
            <DataTable
                columns={dataSourceTableColumns}
                data={dataSources}
                emptyMessage={emptyMessage}
            />
        </div>
    );
}

const dataSourceTableColumns: ColumnDef<DataSource>[] = [
    {
        accessorKey: "link",
        header: "",
        cell: ({ row }) => (
            <DetailsButton href={`integrations/dataSources/${row.getValue("data_source_id")}`} />
        ),
    },
    {
        accessorKey: "data_source_id",
        header: "ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("data_source_id")} />,
    },
    {
        accessorKey: "name",
        header: "Name",
    },
    {
        accessorKey: "description",
        header: "Description",
        cell: ({ row }) => {
            const description: string = row.getValue("description");
            return description.length > 0 ? description : "-";
        },
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
