"use client";

// React and Next.js
import * as React from "react";
import { useRouter } from "next/navigation";

// External libraries
import { ColumnDef } from "@tanstack/react-table";
import { ArrowUpDown, Trash } from "lucide-react";

// Vulkan packages
import { Policy } from "@vulkanlabs/client-open";

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
import { ResourceReference, ResourceTable } from "../resource-table";
import { parseDate } from "../../lib/utils";
import { createGlobalToast } from "../toast";

const toast = createGlobalToast();

export interface PolicyTableConfig {
    projectId?: string;
    deletePolicy: (policyId: string, projectId?: string) => Promise<void>;
    CreatePolicyDialog: React.ReactElement;
    resourcePathTemplate: string;
}

// Create a context for policy deletion
type DeletePolicyContextType = {
    openDeleteDialog: (policy: Policy) => void;
};

const DeletePolicyContext = React.createContext<DeletePolicyContextType | undefined>(undefined);

/**
 * Policies table - full-featured data table for policy management
 * @param {Object} props - Component properties
 * @param {Policy[]} props.policies - Array of policy objects to display
 * @param {PolicyTableConfig} props.config - Table configuration including actions and navigation
 * @returns {JSX.Element} Complete policies table with sorting, actions, delete confirmation
 */
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

    const resourceRef: ResourceReference = {
        type: "Policy",
        idColumn: "policy_id",
        nameColumn: "name",
        pathTemplate: config.resourcePathTemplate,
    };

    return (
        <DeletePolicyContext.Provider value={{ openDeleteDialog }}>
            <ResourceTable
                data={policies}
                columns={policiesTableColumns}
                resourceRef={resourceRef}
                searchOptions={{ column: "name", label: "Name" }}
                defaultSorting={[{ id: "last_updated_at", desc: true }]}
                CreationDialog={config.CreatePolicyDialog}
            />

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
    return [
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
