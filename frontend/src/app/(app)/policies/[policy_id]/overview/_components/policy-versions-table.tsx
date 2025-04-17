"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowUpDown, MoreHorizontal, Trash } from "lucide-react";
import { ColumnDef } from "@tanstack/react-table";
import { toast } from "sonner";

import { DetailsButton } from "@/components/details-button";
import { ShortenedID } from "@/components/shortened-id";
import { ResourceTable } from "@/components/resource-table";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { parseDate } from "@/lib/utils";
import { deletePolicyVersion } from "@/lib/api";

import { Policy } from "@vulkan-server/Policy";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";

import { CreatePolicyVersionDialog } from "./create-version";

// Create a context for policy deletion
type DeletePolicyContextType = {
    openDeleteDialog: (policy: Policy) => void;
};

const DeletePolicyContext = React.createContext<DeletePolicyContextType | undefined>(undefined);

export function PolicyVersionsTable({
    policy,
    policyVersions,
}: {
    policy: Policy;
    policyVersions: PolicyVersion[];
}) {
    const [versionToDelete, setVersionToDelete] = React.useState<PolicyVersion | null>(null);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = React.useState(false);
    const router = useRouter();

    const activeVersions = getActiveVersions(policy);
    const formattedVersions = policyVersions.map((policyVersion) => {
        let status = "inactive";
        if (activeVersions.includes(policyVersion.policy_version_id)) {
            status = "active";
        }
        return {
            ...policyVersion,
            status: status,
        };
    });

    const openDeleteDialog = React.useCallback((policyVersion: PolicyVersion) => {
        setVersionToDelete(policyVersion);
        setIsDeleteDialogOpen(true);
    }, []);

    const closeDeleteDialog = React.useCallback(() => {
        setIsDeleteDialogOpen(false);
    }, []);

    const onDelete = async () => {
        if (!versionToDelete) return;

        try {
            await deletePolicyVersion(versionToDelete.policy_version_id);
            toast("Policy version deleted", {
                description: `Policy version ${versionToDelete.alias} has been deleted.`,
                dismissible: true,
            });
            closeDeleteDialog();
            router.refresh();
        } catch (error) {
            closeDeleteDialog();
            toast.error(`${error.cause}`);
        }
    };

    return (
        <DeletePolicyContext.Provider value={{ openDeleteDialog }}>
            <div>
                <ResourceTable
                    columns={policyVersionsTableColumns}
                    data={formattedVersions}
                    searchFilter={{ column: "alias", label: "Tag" }}
                    CreationDialog={<CreatePolicyVersionDialog policyId={policy.policy_id} />}
                />
            </div>

            <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Policy</DialogTitle>
                        <DialogDescription>
                            {versionToDelete &&
                                `Are you sure you want to delete policy version "${versionToDelete.alias}"? This action cannot be undone.`}
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

const policyVersionsTableColumns: ColumnDef<PolicyVersion>[] = [
    {
        id: "link",
        enableHiding: false,
        cell: ({ row }) => (
            <DetailsButton href={`/policyVersions/${row.getValue("policy_version_id")}/workflow`} />
        ),
    },
    {
        header: "ID",
        accessorKey: "policy_version_id",
        cell: ({ row }) => <ShortenedID id={row.getValue("policy_version_id")} />,
    },
    {
        accessorKey: "alias",
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    className="p-0"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                >
                    <span className="mr-2">Tag</span>
                    <ArrowUpDown className="w-5 h-5" />
                </Button>
            );
        },
        cell: ({ row }) => <div>{row.getValue("alias")}</div>,
    },
    {
        header: "Status",
        accessorKey: "status",
        cell: ({ row }) => {
            const status = row.getValue("status");

            return (
                <Badge variant={status == "active" ? "default" : "outline"}>
                    {row.getValue("status")}
                </Badge>
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
    const policyVersion = row.original;
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
                <DropdownMenuItem
                    onClick={() => navigator.clipboard.writeText(policyVersion.policy_version_id)}
                >
                    Copy Version ID
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                    onClick={() =>
                        router.push(`/policy-versions/${policyVersion.policy_version_id}/workflow`)
                    }
                >
                    View Workflow
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}

function getActiveVersions(policyData) {
    if (policyData.allocation_strategy == null) {
        return [];
    }
    const choiceVersions = policyData.allocation_strategy.choice.map((opt) => {
        return opt.policy_version_id;
    });
    return choiceVersions + policyData.allocation_strategy.shadow;
}
