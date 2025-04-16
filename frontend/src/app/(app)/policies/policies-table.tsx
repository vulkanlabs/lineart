"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ColumnDef } from "@tanstack/react-table";
import { ArrowUpDown, MoreHorizontal, Trash } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DetailsButton } from "@/components/details-button";
import { ShortenedID } from "@/components/shortened-id";
import { ResourceTable } from "@/components/resource-table";
import { parseDate } from "@/lib/utils";
import { deletePolicy } from "@/lib/api";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

import { Policy } from "@vulkan-server/Policy";
import { CreatePolicyDialog } from "./create-dialog";

// Create a context for policy deletion
type DeletePolicyContextType = {
    openDeleteDialog: (policy: Policy) => void;
};

const DeletePolicyContext = React.createContext<DeletePolicyContextType | undefined>(undefined);

export function PoliciesTable({ policies }: { policies: Policy[] }) {
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
            await deletePolicy(policyToDelete.policy_id);
            toast("Policy deleted", {
                description: `Policy ${policyToDelete.name} has been deleted.`,
                dismissible: true,
            });
            closeDeleteDialog();
            router.refresh();
        } catch (error) {
            console.error(error);
            toast.error("Failed to delete policy");
        }
    };

    return (
        <DeletePolicyContext.Provider value={{ openDeleteDialog }}>
            <div>
                <ResourceTable
                    columns={policiesTableColumns}
                    data={policies}
                    searchFilter={{ column: "name", label: "Name" }}
                    CreationDialog={<CreatePolicyDialog />}
                />
            </div>

            <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Policy</DialogTitle>
                        <DialogDescription>
                            {policyToDelete &&
                                `Are you sure you want to delete policy "${policyToDelete.name}"? This action cannot be undone.`}
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

export const policiesTableColumns: ColumnDef<Policy>[] = [
    {
        id: "link",
        enableHiding: false,
        cell: ({ row }) => (
            <DetailsButton href={`/policies/${row.getValue("policy_id")}/overview`} />
        ),
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
            return <PoliciesTableActions row={row} />;
        },
    },
];

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

function PoliciesTableActions({ row }: { row: any }) {
    const policy = row.original;
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
                <DropdownMenuItem onClick={() => navigator.clipboard.writeText(policy.policy_id)}>
                    Copy Policy ID
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                    onClick={() => router.push(`/policies/${policy.policy_id}/overview`)}
                >
                    View Policy
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
