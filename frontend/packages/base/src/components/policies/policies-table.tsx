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
import { DetailsButton, ResourceTable, ShortenedID } from "../../index";
import { Policy } from "@vulkanlabs/client-open";

// Local imports
import { parseDate } from "../../lib/utils";

export interface PolicyTableConfig {
    projectId?: string;
    withProject?: (path: string, projectId: string) => string;
    deletePolicy: (policyId: string, projectId?: string) => Promise<void>;
    CreatePolicyDialog: React.ReactElement;
}

// Create a context for policy deletion
type DeletePolicyContextType = {
    openDeleteDialog: (policy: Policy) => void;
};

const DeletePolicyContext = React.createContext<DeletePolicyContextType | undefined>(undefined);

export function PoliciesTable({
    policies,
    config,
}: {
    policies: Policy[];
    config: PolicyTableConfig;
}) {
    const [policyToDelete, setPolicyToDelete] = React.useState<Policy | null>(null);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = React.useState(false);
    const router = useRouter();

    const openDeleteDialog = React.useCallback((policy: Policy) => {
        setPolicyToDelete(policy);
        setIsDeleteDialogOpen(true);
    }, []);

    const closeDeleteDialog = React.useCallback(() => {
        setIsDeleteDialogOpen(false);
    }, []);

    const onDelete = async () => {
        if (!policyToDelete) return;

        try {
            await config.deletePolicy(policyToDelete.policy_id, config.projectId);
            toast("Policy deleted", {
                description: `Policy ${policyToDelete.name} has been deleted.`,
                dismissible: true,
            });
            closeDeleteDialog();
            router.refresh();
        } catch (error: any) {
            closeDeleteDialog();
            toast.error(`${error.cause || error.message || "An unknown error occurred"}`);
        }
    };

    const policiesTableColumns: ColumnDef<Policy>[] = getTableColumns(config);

    return (
        <DeletePolicyContext.Provider value={{ openDeleteDialog }}>
            <div>
                <ResourceTable
                    columns={policiesTableColumns}
                    data={policies}
                    searchOptions={{ column: "name", label: "Name" }}
                    CreationDialog={config.CreatePolicyDialog}
                />
            </div>

            <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Policy</DialogTitle>
                        <DialogDescription>
                            {policyToDelete &&
                                `Are you sure you want to delete policy "${policyToDelete.name}"?` +
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
        </DeletePolicyContext.Provider>
    );
}

function getTableColumns(config: PolicyTableConfig): ColumnDef<Policy>[] {
    const buildHref = (policyId: string): string => {
        const basePath = `/policies/${policyId}/overview`;
        if (config.projectId && config.withProject) {
            return config.withProject(basePath, config.projectId);
        }
        return basePath;
    };

    return [
        {
            id: "link",
            enableHiding: false,
            cell: ({ row }) => <DetailsButton href={buildHref(row.getValue("policy_id"))} />,
        },
        {
            header: "ID",
            accessorKey: "policy_id",
            cell: ({ row }) => <ShortenedID id={row.getValue("policy_id")} />,
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
            header: "Active Version",
            accessorKey: "active_policy_version_id",
            cell: ({ row }) =>
                row.getValue("active_policy_version_id") == null ? (
                    "-"
                ) : (
                    <ShortenedID id={row.getValue("active_policy_version_id")} />
                ),
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
            cell: ({ row }) => {
                return <DeletePolicyButton policy={row.original} />;
            },
        },
        {
            id: "actions",
            enableHiding: false,
            cell: ({ row }) => {
                return <PoliciesTableActions row={row} config={config} />;
            },
        },
    ];
}

function DeletePolicyButton({ policy }: { policy: Policy }) {
    const deleteContext = React.useContext(DeletePolicyContext);

    if (!deleteContext) {
        throw new Error("DeletePolicyButton must be used within a DeletePolicyContext Provider");
    }
    return (
        <Button
            variant="ghost"
            className="p-0"
            onClick={() => deleteContext.openDeleteDialog(policy)}
        >
            <span className="sr-only">Delete</span>
            <Trash className="h-5 w-5" />
        </Button>
    );
}

function PoliciesTableActions({ row, config }: { row: any; config: PolicyTableConfig }) {
    const policy = row.original;
    const router = useRouter();

    const buildHref = (policyId: string): string => {
        const basePath = `/policies/${policyId}/overview`;
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
                <DropdownMenuItem onClick={() => navigator.clipboard.writeText(policy.policy_id)}>
                    Copy Policy ID
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => router.push(buildHref(policy.policy_id))}>
                    View Policy
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
