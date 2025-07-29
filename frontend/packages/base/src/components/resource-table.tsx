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
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuCheckboxItem,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

export interface SearchFilterOptions {
    column: string;
    label: string;
}

export interface ResourceTableProps<TData, TValue> {
    data: TData[];
    columns: ColumnDef<TData, TValue>[];
    pageSize?: number;
    searchOptions?: SearchFilterOptions;
    enableColumnHiding?: boolean;
    disableFilters?: boolean;
    CreationDialog?: React.ReactNode;
}

export function ResourceTable<TData, TValue>({
    data,
    columns,
    pageSize,
    searchOptions,
    enableColumnHiding,
    disableFilters,
    CreationDialog,
}: ResourceTableProps<TData, TValue>) {
    const [sorting, setSorting] = React.useState<SortingState>([]);
    const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
    const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({});
    const [pagination, setPagination] = React.useState({ pageIndex: 0, pageSize: pageSize ?? 5 });
    const [rowSelection, setRowSelection] = React.useState({});

    const router = useRouter();

    const table = useReactTable({
        data,
        columns,
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
                                <TableCell colSpan={columns.length} className="h-24 text-center">
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
    resourceType: string;
    resourceIdColumn: string;
    resourceNameColumn: string;
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
    pageSize,
    searchOptions,
    deleteOptions,
    enableColumnHiding,
    CreationDialog,
}: DeletableResourceTableProps<TData, TValue>) {
    const { resourceType, resourceIdColumn, resourceNameColumn, deleteResourceFunction } =
        deleteOptions;
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
            await deleteResourceFunction(resourceToDelete[resourceIdColumn]);
            toast(`${resourceType} deleted`, {
                description: `${resourceType} ${resourceToDelete[resourceNameColumn]} has been deleted.`,
                dismissible: true,
            });
            closeDeleteDialog();
            router.refresh();
        } catch (error) {
            closeDeleteDialog();
            toast.error(`${(error as Error)?.message || "An error occurred"}`);
        }
    };

    return (
        <DeleteResourceContext.Provider value={{ openDeleteDialog }}>
            <div>
                <ResourceTable
                    data={data}
                    columns={columns}
                    pageSize={pageSize}
                    searchOptions={searchOptions}
                    enableColumnHiding={enableColumnHiding}
                    CreationDialog={CreationDialog}
                />
            </div>

            <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete {resourceType}</DialogTitle>
                        <DialogDescription>
                            {resourceToDelete &&
                                `Are you sure you want to delete ${resourceType} "${resourceToDelete[resourceNameColumn]}"? This action cannot be undone.`}
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

export function DeletableResourceTableActions({
    row,
    resourceId,
    resourcePageLink,
}: {
    row: any;
    resourceId: string;
    resourcePageLink: string;
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
                <DropdownMenuItem onClick={() => router.push(resourcePageLink)}>
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
