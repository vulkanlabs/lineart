"use client";

// External libraries
import { ArrowUpDown } from "lucide-react";
import { ColumnDef } from "@tanstack/react-table";

// Vulkan packages
import { DataSource } from "@vulkanlabs/client-open";

// Local imports
import { Button } from "../ui";
import { ShortenedID } from "../shortened-id";
import {
    DeletableResourceTable,
    SearchFilterOptions,
    DeleteResourceOptions,
    ResourceReference,
} from "../resource-table";
import { parseDate } from "../../lib/utils";

export interface DataSourceTableConfig {
    projectId?: string;
    deleteDataSource: (id: string, projectId?: string) => Promise<void>;
    CreateDataSourceDialog: React.ReactElement;
    resourcePathTemplate: string;
}

/**
 * Data sources management table - displays and manages data source connections
 * @param {Object} props - Component properties
 * @param {DataSource[]} props.dataSources - Array of data source objects to display
 * @param {DataSourceTableConfig} props.config - Table configuration including delete actions and navigation
 * @returns {JSX.Element} Complete table with search, sorting, and management actions
 */
export function DataSourcesTable({
    dataSources,
    config,
}: {
    dataSources: DataSource[];
    config: DataSourceTableConfig;
}) {
    const resourceRef: ResourceReference = {
        type: "Data Source",
        idColumn: "data_source_id",
        nameColumn: "name",
        pathTemplate: config.resourcePathTemplate,
    };

    const deleteOptions: DeleteResourceOptions = {
        deleteResourceFunction: (id: string) => config.deleteDataSource(id, config.projectId),
    };

    const columns = getDataSourceTableColumns(config);

    return (
        <DeletableResourceTable
            data={dataSources}
            columns={columns}
            resourceRef={resourceRef}
            searchOptions={{ column: "name", label: "Name" }}
            defaultSorting={[{ id: "last_updated_at", desc: true }]}
            CreationDialog={config.CreateDataSourceDialog}
            deleteOptions={deleteOptions}
        />
    );
}

function getDataSourceTableColumns(config: DataSourceTableConfig): ColumnDef<DataSource>[] {
    return [
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
    ];
}
