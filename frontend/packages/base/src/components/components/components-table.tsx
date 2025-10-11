"use client";

// React
import * as React from "react";
import { Suspense } from "react";
import { useRouter } from "next/navigation";

// External libraries
import { ColumnDef } from "@tanstack/react-table";
import { ArrowUpDown, Trash } from "lucide-react";

// Vulkan packages
import { type Component } from "@vulkanlabs/client-open";

// Local imports
import {
    Button,
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "../ui";
import { ShortenedID } from "../shortened-id";
import { ResourceTable } from "../resource-table";
import { parseDate } from "../../lib/utils";
import { createGlobalToast } from "../toast";
import { ResourceReference, DisplayOptions } from "../resource-table";

const toast = createGlobalToast();

export interface ComponentsTableConfig {
    projectId?: string;
    deleteComponent: (componentName: string, projectId?: string) => Promise<void>;
    CreateComponentDialog: React.ReactElement;
    resourcePathTemplate: string;
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
    config,
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
            await config.deleteComponent(componentToDelete.name, config.projectId);
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

    const resourceRef: ResourceReference = {
        type: "Component",
        idColumn: "name",
        nameColumn: "name",
        pathTemplate: config.resourcePathTemplate,
    };

    const displayOptions: DisplayOptions = {
        pageSize: 10,
    };

    return (
        <DeleteComponentContext.Provider value={{ openDeleteDialog }}>
            <Suspense fallback={<div>Loading...</div>}>
                <ResourceTable
                    data={components}
                    columns={columns}
                    resourceRef={resourceRef}
                    displayOptions={{ pageSize: 10 }}
                    searchOptions={{ column: "name", label: "Name" }}
                    defaultSorting={[{ id: "last_updated_at", desc: true }]}
                    CreationDialog={config.CreateComponentDialog}
                />
            </Suspense>

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
        </DeleteComponentContext.Provider>
    );
}

function getComponentsTableColumns(config: ComponentsTableConfig): ColumnDef<Component>[] {
    return [
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
        {
            id: "delete",
            enableHiding: false,
            cell: ({ row }: any) => {
                return <DeleteComponentButton component={row.original} />;
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
