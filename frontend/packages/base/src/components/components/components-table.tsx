"use client";

// React and Next.js
import * as React from "react";
import { useRouter } from "next/navigation";

// External libraries
import { ColumnDef } from "@tanstack/react-table";
import { ArrowUpDown, MoreHorizontal, Trash } from "lucide-react";
import { toast } from "sonner";

// Vulkan packages
import {
    Button,
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@vulkanlabs/base/ui";
import { DetailsButton, ResourceTable, DataTable, ShortenedID } from "../../index";
import { type Component } from "@vulkanlabs/client-open";

// Local imports
import { parseDate } from "../../lib/utils";

export interface ComponentsTableConfig {
    projectId?: string;
    withProject?: (path: string, projectId: string) => string;
    deleteComponent?: (componentId: string, projectId?: string) => Promise<void>;
    CreateComponentDialog?: React.ReactElement;
    mode?: "full" | "simple"; // full = OSS-style, simple = SaaS-style
}

// Create a context for component deletion
type DeleteComponentContextType = {
    openDeleteDialog: (component: Component) => void;
};

const DeleteComponentContext = React.createContext<DeleteComponentContextType | undefined>(
    undefined,
);

export function ComponentsTable({ 
    components, 
    config 
}: { 
    components: Component[]; 
    config: ComponentsTableConfig;
}) {
    const [componentToDelete, setComponentToDelete] = React.useState<Component | null>(null);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = React.useState(false);
    const router = useRouter();

    const openDeleteDialog = React.useCallback((component: Component) => {
        setComponentToDelete(component);
        setIsDeleteDialogOpen(true);
    }, []);

    const closeDeleteDialog = React.useCallback(() => {
        setIsDeleteDialogOpen(false);
    }, []);

    const onDelete = async () => {
        if (!componentToDelete || !config.deleteComponent) return;

        try {
            await config.deleteComponent(componentToDelete.component_id, config.projectId);
            toast("Component deleted", {
                description: `Component ${componentToDelete.name} has been deleted.`,
                dismissible: true,
            });
            closeDeleteDialog();
            router.refresh();
        } catch (error: any) {
            closeDeleteDialog();
            toast.error(`${error.cause || error.message || "An unknown error occurred"}`);
        }
    };

    const columns = getComponentsTableColumns(config);

    // Use simple DataTable for SaaS-style, full ResourceTable for OSS-style
    if (config.mode === "simple") {
        return (
            <div>
                <Button onClick={() => router.refresh()}>Refresh</Button>
                <div className="mt-4">
                    <DataTable
                        columns={columns}
                        data={components}
                        emptyMessage="Create a component to start using it in your workflows."
                    />
                </div>
            </div>
        );
    }

    // Full OSS-style table with deletion dialog
    return (
        <DeleteComponentContext.Provider value={{ openDeleteDialog }}>
            <div>
                <ResourceTable
                    columns={columns}
                    data={components}
                    searchOptions={{ column: "name", label: "Name" }}
                    CreationDialog={config.CreateComponentDialog}
                    pageSize={10}
                    enableColumnHiding={false}
                    disableFilters={false}
                />
            </div>

            {config.deleteComponent && (
                <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                    <DialogContent>
                        <DialogHeader className="">
                            <DialogTitle>Delete Component</DialogTitle>
                            <DialogDescription>
                                {componentToDelete &&
                                    `Are you sure you want to delete component "${componentToDelete.name}"?` +
                                        "This action cannot be undone."}
                            </DialogDescription>
                        </DialogHeader>
                        <DialogFooter className="">
                            <Button variant="outline" onClick={closeDeleteDialog}>
                                Cancel
                            </Button>
                            <Button variant="destructive" onClick={onDelete}>
                                Delete
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            )}
        </DeleteComponentContext.Provider>
    );
}

function getComponentsTableColumns(config: ComponentsTableConfig): ColumnDef<Component>[] {
    const buildHref = (componentId: string): string => {
        const basePath = `/components/${componentId}`;
        if (config.projectId && config.withProject) {
            return config.withProject(basePath, config.projectId);
        }
        return basePath;
    };

    // Simple columns for SaaS-style
    if (config.mode === "simple") {
        return [
            {
                accessorKey: "link",
                header: "",
                cell: ({ row }) => (
                    <DetailsButton href={buildHref(row.getValue("component_id"))} />
                ),
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
    }

    // Full columns for OSS-style
    return [
        {
            id: "link",
            enableHiding: false,
            cell: ({ row }) => (
                <DetailsButton href={buildHref(row.getValue("component_id"))} />
            ),
        },
        {
            header: "ID",
            accessorKey: "component_id",
            cell: ({ row }) => <ShortenedID id={row.getValue("component_id")} />,
        },
        {
            header: "Icon",
            accessorKey: "icon",
            cell: ({ row }) => {
                const icon = row.getValue("icon") as string;
                return icon ? (
                    <div className="flex items-center gap-2">
                        <img
                            src={icon}
                            alt="Component icon"
                            className="h-8 w-8 object-contain rounded"
                        />
                    </div>
                ) : (
                    "-"
                );
            },
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
            header: "Description",
            accessorKey: "description",
            cell: ({ row }) => {
                return (
                    <div className="min-w-52 max-w-52 overflow-hidden whitespace-nowrap text-ellipsis">
                        {row.getValue("description") || "-"}
                    </div>
                );
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
        ...(config.deleteComponent ? [{
            id: "delete" as const,
            enableHiding: false,
            cell: ({ row }: any) => {
                return <DeleteComponentButton component={row.original} />;
            },
        }] : []),
        {
            id: "actions",
            enableHiding: false,
            cell: ({ row }: any) => {
                return <ComponentsTableActions row={row} config={config} />;
            },
        },
    ];
}

function DeleteComponentButton({ component }: { component: Component }) {
    const deleteContext = React.useContext(DeleteComponentContext);

    if (!deleteContext) {
        throw new Error(
            "DeleteComponentButton must be used within a DeleteComponentContext Provider",
        );
    }
    return (
        <Button
            variant="ghost"
            className="p-0"
            onClick={() => deleteContext.openDeleteDialog(component)}
        >
            <span className="sr-only">Delete</span>
            <Trash className="h-5 w-5" />
        </Button>
    );
}

function ComponentsTableActions({ row, config }: { row: any; config: ComponentsTableConfig }) {
    const component = row.original;
    const router = useRouter();

    const buildHref = (componentId: string): string => {
        const basePath = `/components/${componentId}`;
        if (config.projectId && config.withProject) {
            return config.withProject(basePath, config.projectId);
        }
        return basePath;
    };

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
                <DropdownMenuItem
                    onClick={() => navigator.clipboard.writeText(component.component_id)}
                >
                    Copy Component ID
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                    onClick={() => router.push(buildHref(component.component_id))}
                >
                    View Component
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}