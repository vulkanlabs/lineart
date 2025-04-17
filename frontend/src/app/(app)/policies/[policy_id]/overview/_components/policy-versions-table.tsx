"use client";

import { ArrowUpDown } from "lucide-react";
import { ColumnDef } from "@tanstack/react-table";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DetailsButton } from "@/components/details-button";
import { ShortenedID } from "@/components/shortened-id";
import {
    DeletableResourceTable,
    DeletableResourceTableActions,
    SearchFilterOptions,
    DeleteResourceOptions,
} from "@/components/resource-table";

import { parseDate } from "@/lib/utils";
import { deletePolicyVersion } from "@/lib/api";

import { Policy } from "@vulkan-server/Policy";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";

import { CreatePolicyVersionDialog } from "./create-version";

export function PolicyVersionsTable({
    policy,
    policyVersions,
}: {
    policy: Policy;
    policyVersions: PolicyVersion[];
}) {
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

    const searchOptions: SearchFilterOptions = {
        column: "alias",
        label: "Tag",
    };

    const deleteOptions: DeleteResourceOptions = {
        resourceType: "Policy Version",
        resourceIdColumn: "policy_version_id",
        resourceNameColumn: "alias",
        deleteResourceFunction: deletePolicyVersion,
    };

    return (
        <DeletableResourceTable
            columns={policyVersionsTableColumns}
            data={formattedVersions}
            searchOptions={searchOptions}
            deleteOptions={deleteOptions}
            CreationDialog={<CreatePolicyVersionDialog policyId={policy.policy_id} />}
        />
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
        id: "actions",
        enableHiding: false,
        cell: ({ row }) => {
            const policyVersionId = row.original.policy_version_id;
            const pageLink = `/policyVersions/${policyVersionId}/workflow`;
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

function getActiveVersions(policyData) {
    if (policyData.allocation_strategy == null) {
        return [];
    }
    const choiceVersions = policyData.allocation_strategy.choice.map((opt) => {
        return opt.policy_version_id;
    });
    return choiceVersions + policyData.allocation_strategy.shadow;
}
