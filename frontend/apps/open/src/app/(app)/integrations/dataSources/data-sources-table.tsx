"use client";

// External libraries
import { ArrowUpDown } from "lucide-react";
import { ColumnDef } from "@tanstack/react-table";

// Vulkan packages
import { Button } from "@vulkanlabs/base/ui";
import {
    DetailsButton,
    ShortenedID,
    DeletableResourceTable,
    DeletableResourceTableActions,
    SearchFilterOptions,
    DeleteResourceOptions,
} from "@vulkanlabs/base";
import { DataSource } from "@vulkanlabs/client-open";

// Local imports
import { parseDate } from "@/lib/utils";
import { deleteDataSource } from "@/lib/api";
import { OSSCreateDataSourceDialog } from "../../../../components/data-sources/create-dialog";

export default function DataSourcesTable({ dataSources }: { dataSources: DataSource[] }) {
    const searchOptions: SearchFilterOptions = {
        column: "name",
        label: "Name",
    };

    const deleteOptions: DeleteResourceOptions = {
        resourceType: "Data Source",
        resourceIdColumn: "data_source_id",
        resourceNameColumn: "name",
        deleteResourceFunction: deleteDataSource,
    };

    return (
        <DeletableResourceTable
            columns={dataSourceTableColumns}
            data={dataSources}
            searchOptions={searchOptions}
            deleteOptions={deleteOptions}
            CreationDialog={<OSSCreateDataSourceDialog />}
        />
    );
}

const dataSourceTableColumns: ColumnDef<DataSource>[] = [
    {
        accessorKey: "link",
        header: "",
        cell: ({ row }) => (
            <DetailsButton href={`/integrations/dataSources/${row.getValue("data_source_id")}`} />
        ),
    },
    {
        header: "ID",
        accessorKey: "data_source_id",
        cell: ({ row }) => <ShortenedID id={row.getValue("data_source_id")} />,
    },
    {
        accessorKey: "name",
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    className="p-0"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                >
                    <span className="mr-2">Name</span>
                    <ArrowUpDown className="w-5 h-5" />
                </Button>
            );
        },
        cell: ({ row }) => <div>{row.getValue("name")}</div>,
    },
    {
        accessorKey: "description",
        header: "Description",
        cell: ({ row }) => {
            const description: string = row.getValue("description");
            return description?.length > 0 ? description : "-";
        },
    },
    {
        accessorKey: "created_at",
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    className="p-0"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                >
                    <span className="mr-2">Created At</span>
                    <ArrowUpDown className="w-5 h-5" />
                </Button>
            );
        },
        cell: ({ row }) => parseDate(row.getValue("created_at")),
    },
    {
        accessorKey: "last_updated_at",
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    className="p-0"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                >
                    <span className="mr-2">Last Updated At</span>
                    <ArrowUpDown className="w-5 h-5" />
                </Button>
            );
        },
        cell: ({ row }) => parseDate(row.getValue("last_updated_at")),
    },
    {
        id: "actions",
        enableHiding: false,
        cell: ({ row }) => {
            const policyVersionId = row.original.data_source_id;
            const pageLink = `/integrations/dataSources/${row.getValue("data_source_id")}`;
            return (
                <DeletableResourceTableActions
                    row={row}
                    resourceId={policyVersionId}
                    resourcePageLink={pageLink}
                />
            );
        },
    },
];
