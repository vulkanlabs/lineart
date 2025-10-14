"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
    ColumnDef,
    ColumnFiltersState,
    SortingState,
    VisibilityState,
    flexRender,
    getCoreRowModel,
    getFilteredRowModel,
    getPaginationRowModel,
    getSortedRowModel,
    useReactTable,
} from "@tanstack/react-table";
import { ChevronDown, Copy, ExternalLink, MoreHorizontal, RefreshCcw, Trash } from "lucide-react";

import { Button } from "./ui/button";
import {
    DropdownMenu,
    DropdownMenuCheckboxItem,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Input } from "./ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "./ui/dialog";
import { DetailsButton } from "./details-button";
import { createGlobalToast } from "./toast";

const toast = createGlobalToast();

export interface SearchFilterOptions {
    column: string;
    label: string;
}

export interface ResourceReference {
    type: string;
    idColumn: string;
    nameColumn: string;
    pathTemplate: string;
}

export interface DisplayOptions {
    pageSize?: number;
    enableColumnHiding?: boolean;
    disableActions?: boolean;
    disableFilters?: boolean;
}

export interface ResourceAction {
    label: string;
    icon: React.ComponentType<any>;
    onClick: (resource: any) => void;
}

export interface ResourceTableProps<TData, TValue> {
    data: TData[];
    columns: ColumnDef<TData, TValue>[];
    resourceRef: ResourceReference;
    CreationDialog?: React.ReactNode;
    displayOptions?: DisplayOptions;
    searchOptions?: SearchFilterOptions;
    defaultSorting?: SortingState;
    extraActions?: ResourceAction[];
}

export function ResourceTable<TData, TValue>({
    data,
    columns,
    resourceRef,
    CreationDialog,
    displayOptions,
    searchOptions,
    defaultSorting,
    extraActions,
}: ResourceTableProps<TData, TValue>) {
    const { pageSize, enableColumnHiding, disableFilters, disableActions } = displayOptions || {};

    // try last_updated_at first, then created_at, as DESC
    const getDefaultSorting = (): SortingState => {
        if (defaultSorting) return defaultSorting;

        const columnIds = columns
            .map((col) => {
                // Check if the column has accessorKey property
                if ("accessorKey" in col && typeof col.accessorKey === "string")
                    return col.accessorKey;
                return col.id;
            })
            .filter(Boolean);

        if (columnIds.includes("last_updated_at")) return [{ id: "last_updated_at", desc: true }];
        if (columnIds.includes("created_at")) return [{ id: "created_at", desc: true }];

        return [];
    };

    const [sorting, setSorting] = React.useState<SortingState>(getDefaultSorting());
    const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
    const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({});
    const [pagination, setPagination] = React.useState({ pageIndex: 0, pageSize: pageSize ?? 5 });
    const [rowSelection, setRowSelection] = React.useState({});

    const router = useRouter();

    let tableColumns = React.useMemo(() => [...columns], [columns]);
    // Always add link column at the start
    tableColumns.unshift({
        id: "link",
        enableHiding: false,
        cell: ({ row }) => (
            <DetailsButton
                href={renderResourcePath(
                    resourceRef.pathTemplate,
                    row.getValue(resourceRef.idColumn),
                )}
            />
        ),
    });

    if (!disableActions) {
        tableColumns.push({
            id: "actions",
            enableHiding: false,
            cell: ({ row }) => (
                <BaseResourceTableActions
                    row={row}
                    resourceRef={resourceRef}
                    extraActions={extraActions}
                />
            ),
        });
    }

    const table = useReactTable({
        data,
        columns: tableColumns,
        onSortingChange: setSorting,
        onColumnFiltersChange: setColumnFilters,
        getCoreRowModel: getCoreRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        onColumnVisibilityChange: setColumnVisibility,
        onRowSelectionChange: setRowSelection,
        onPaginationChange: setPagination,
        state: {
            sorting,
            columnFilters,
            columnVisibility,
            rowSelection,
            pagination,
        },
    });

    return (
        <div className="w-full">
            {disableFilters ? null : (
                <div className="flex items-center py-4">
                    <div className="flex items-center gap-2">
                        {searchOptions && (
                            <Input
                                placeholder={`Filter ${searchOptions.label}...`}
                                value={
                                    (table
                                        .getColumn(searchOptions.column)
                                        ?.getFilterValue() as string) ?? ""
                                }
                                onChange={(event) =>
                                    table
                                        .getColumn(searchOptions.column)
                                        ?.setFilterValue(event.target.value)
                                }
                                className="max-w-sm"
                            />
                        )}
                        <Button variant="outline" onClick={() => router.refresh()}>
                            <RefreshCcw className="h-4 w-4" />
                        </Button>
                        {CreationDialog}
                    </div>
                    <div className="flex items-center gap-2">
                        {enableColumnHiding && (
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="outline">
                                        Columns <ChevronDown />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                    {table
                                        .getAllColumns()
                                        .filter((column) => column.getCanHide())
                                        .map((column) => {
                                            return (
                                                <DropdownMenuCheckboxItem
                                                    key={column.id}
                                                    className="capitalize"
                                                    checked={column.getIsVisible()}
                                                    onCheckedChange={(value) =>
                                                        column.toggleVisibility(!!value)
                                                    }
                                                >
                                                    {column.id}
                                                </DropdownMenuCheckboxItem>
                                            );
                                        })}
                                </DropdownMenuContent>
                            </DropdownMenu>
                        )}
                    </div>
                </div>
            )}
            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        {table.getHeaderGroups().map((headerGroup) => (
                            <TableRow key={headerGroup.id}>
                                {headerGroup.headers.map((header) => {
                                    return (
                                        <TableHead key={header.id}>
                                            {header.isPlaceholder
                                                ? null
                                                : flexRender(
                                                      header.column.columnDef.header,
                                                      header.getContext(),
                                                  )}
                                        </TableHead>
                                    );
                                })}
                            </TableRow>
                        ))}
                    </TableHeader>
                    <TableBody>
                        {table.getRowModel().rows?.length ? (
                            table.getRowModel().rows.map((row) => (
                                <TableRow
                                    key={row.id}
                                    data-state={row.getIsSelected() && "selected"}
                                >
                                    {row.getVisibleCells().map((cell) => (
                                        <TableCell key={cell.id}>
                                            {flexRender(
                                                cell.column.columnDef.cell,
                                                cell.getContext(),
                                            )}
                                        </TableCell>
                                    ))}
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell
                                    colSpan={tableColumns.length}
                                    className="h-24 text-center"
                                >
                                    No results.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
            {table.getPageCount() > 1 && (
                <div className="flex items-center justify-end space-x-2 py-4">
                    <div className="flex-1 text-sm text-muted-foreground">
                        <span>
                            Page {table.getState().pagination.pageIndex + 1} of{" "}
                            {table.getPageCount()}
                        </span>
                    </div>
                    <div className="space-x-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => table.previousPage()}
                            disabled={!table.getCanPreviousPage()}
                        >
                            Previous
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => table.nextPage()}
                            disabled={!table.getCanNextPage()}
                        >
                            Next
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}

export interface DeleteResourceOptions {
    deleteResourceFunction: (resourceId: string) => Promise<void>;
}
export interface DeletableResourceTableProps<TData, TValue>
    extends ResourceTableProps<TData, TValue> {
    deleteOptions: DeleteResourceOptions;
}

type DeleteResourceContextType = {
    openDeleteDialog: (resource: any) => void;
};

export const DeleteResourceContext = React.createContext<DeleteResourceContextType | undefined>(
    undefined,
);

export function DeletableResourceTable<TData, TValue>({
    data,
    columns,
    resourceRef,
    CreationDialog,
    displayOptions,
    searchOptions,
    defaultSorting,
    extraActions,
    deleteOptions,
}: DeletableResourceTableProps<TData, TValue>) {
    const { deleteResourceFunction } = deleteOptions;
    const [resourceToDelete, setResourceToDelete] = React.useState(null);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = React.useState(false);
    const router = useRouter();

    const openDeleteDialog = React.useCallback((resource: any) => {
        setResourceToDelete(resource);
        setIsDeleteDialogOpen(true);
    }, []);

    const closeDeleteDialog = React.useCallback(() => {
        setIsDeleteDialogOpen(false);
    }, []);

    const onDelete = async () => {
        if (!resourceToDelete) return;

        try {
            await deleteResourceFunction(resourceToDelete[resourceRef.idColumn]);
            toast(`${resourceRef.type} deleted`, {
                description: `${resourceRef.type} ${resourceToDelete[resourceRef.nameColumn]} has been deleted.`,
                dismissible: true,
            });
            closeDeleteDialog();
            router.refresh();
        } catch (error) {
            closeDeleteDialog();
            toast.error(`${(error as Error)?.message || "An unknown error occurred"}`);
        }
    };

    const deleteAction: ResourceAction = {
        onClick: async (resource) => {
            await sleep(100);
            openDeleteDialog(resource);
        },
        label: "Delete",
        icon: Trash,
    };

    extraActions = extraActions ? [deleteAction, ...extraActions] : [deleteAction];

    return (
        <DeleteResourceContext.Provider value={{ openDeleteDialog }}>
            <ResourceTable
                data={data}
                columns={columns}
                resourceRef={resourceRef}
                CreationDialog={CreationDialog}
                displayOptions={displayOptions}
                searchOptions={searchOptions}
                extraActions={extraActions}
                defaultSorting={defaultSorting}
            />

            <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete {resourceRef.type}</DialogTitle>
                        <DialogDescription>
                            {resourceToDelete &&
                                `Are you sure you want to delete ${resourceRef.type} "${resourceToDelete[resourceRef.nameColumn]}"? ` +
                                    "This action cannot be undone."}
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={closeDeleteDialog}>
                            Cancel
                        </Button>
                        <Button variant="destructive" onClick={onDelete}>
                            Delete
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </DeleteResourceContext.Provider>
    );
}

export function BaseResourceTableActions({
    row,
    resourceRef,
    extraActions,
}: {
    row: any;
    resourceRef: ResourceReference;
    extraActions?: ResourceAction[];
}) {
    const router = useRouter();
    const resource = row.original;
    const resourceId = row.original[resourceRef.idColumn];

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="h-8 w-8 p-0">
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <DropdownMenuLabel>Actions</DropdownMenuLabel>
                <DropdownMenuItem onClick={() => navigator.clipboard.writeText(resourceId)}>
                    <div className="flex items-center gap-2">
                        <Copy className="h-5 w-5" />
                        <span>Copy ID</span>
                    </div>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                    onClick={() =>
                        router.push(renderResourcePath(resourceRef.pathTemplate, resourceId))
                    }
                >
                    <div className="flex items-center gap-2">
                        <ExternalLink className="h-5 w-5" />
                        <span>View</span>
                    </div>
                </DropdownMenuItem>
                {extraActions &&
                    extraActions.map((action) => (
                        <DropdownMenuItem
                            onClick={async () => {
                                await action.onClick(resource);
                            }}
                        >
                            <div className="flex items-center gap-2">
                                <action.icon className="h-5 w-5" />
                                <span>{action.label}</span>
                            </div>
                        </DropdownMenuItem>
                    ))}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}

export function DeletableResourceTableActions({
    row,
    resourceId,
    resourcePagePath,
}: {
    row: any;
    resourceId: string;
    resourcePagePath: string;
}) {
    const deleteContext = React.useContext(DeleteResourceContext);
    const resource = row.original;
    const router = useRouter();

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="h-8 w-8 p-0">
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <DropdownMenuLabel>Actions</DropdownMenuLabel>
                <DropdownMenuItem onClick={() => navigator.clipboard.writeText(resourceId)}>
                    <div className="flex items-center gap-2">
                        <Copy className="h-5 w-5" />
                        <span>Copy ID</span>
                    </div>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => router.push(resourcePagePath)}>
                    <div className="flex items-center gap-2">
                        <ExternalLink className="h-5 w-5" />
                        <span>View</span>
                    </div>
                </DropdownMenuItem>
                <DropdownMenuItem
                    onClick={async () => {
                        await sleep(100);
                        deleteContext?.openDeleteDialog(resource);
                    }}
                >
                    <div className="flex items-center gap-2">
                        <Trash className="h-5 w-5" />
                        <span>Delete</span>
                    </div>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export function DeleteResourceButton({ resource }: { resource: any }) {
    const deleteContext = React.useContext(DeleteResourceContext);

    if (!deleteContext) {
        throw new Error(
            "DeleteResourceButton must be used within a DeleteResourceContext Provider",
        );
    }
    return (
        <Button
            variant="ghost"
            className="p-0"
            onClick={() => deleteContext.openDeleteDialog(resource)}
        >
            <span className="sr-only">Delete</span>
            <Trash className="h-5 w-5" />
        </Button>
    );
}

export function renderResourcePath(resourcePathTemplate: string, resourceId: string) {
    return resourcePathTemplate.replace("{resourceId}", resourceId);
}
