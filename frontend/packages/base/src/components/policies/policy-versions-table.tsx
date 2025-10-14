"use client";

// External libraries
import { useMemo } from "react";
import { ArrowUpDown } from "lucide-react";
import { ColumnDef } from "@tanstack/react-table";

// Vulkan packages
import type { Policy, PolicyVersion } from "@vulkanlabs/client-open";
import { WorkflowStatus } from "@vulkanlabs/client-open";

// Local imports
import { Button, Badge } from "../ui";
import {
    ShortenedID,
    DeletableResourceTable,
    SearchFilterOptions,
    DeleteResourceOptions,
} from "../..";
import { ResourceReference } from "../resource-table";
import { parseDate } from "../../lib/utils";

export interface PolicyVersionsTableConfig {
    policy: Policy;
    policyVersions: PolicyVersion[];
    deletePolicyVersion: (versionId: string) => Promise<any>;
    CreateVersionDialog: React.ComponentType<any>;
    resourcePathTemplate: string;
}

/**
 * Policy versions table component
 * @param {Object} props - Component properties
 * @param {PolicyVersionsTableConfig} props.config - Table configuration including data and handlers
 * @returns {JSX.Element} Table displaying policy versions with actions
 */
export function PolicyVersionsTable({ config }: { config: PolicyVersionsTableConfig }) {
    const {
        policy,
        policyVersions,
        deletePolicyVersion,
        CreateVersionDialog,
        resourcePathTemplate,
    } = config;
    const activeVersions = useMemo(() => getActiveVersions(policy), [policy]);

    const formattedVersions = useMemo(
        () =>
            policyVersions.map((policyVersion: PolicyVersion) => {
                const activeStatus = activeVersions.includes(policyVersion.policy_version_id)
                    ? "active"
                    : "inactive";

                // Use the actual status from the backend if available, or fallback to INVALID
                // In the future, this will always come from the backend
                const validationStatus: WorkflowStatus =
                    policyVersion.workflow?.status || WorkflowStatus.Invalid;

                return {
                    ...policyVersion,
                    validationStatus,
                    activeStatus,
                };
            }),
        [policyVersions, activeVersions],
    );

    const resourceRef: ResourceReference = {
        type: "Policy Version",
        idColumn: "policy_version_id",
        nameColumn: "alias",
        pathTemplate: resourcePathTemplate,
    };

    const deleteOptions: DeleteResourceOptions = {
        deleteResourceFunction: deletePolicyVersion,
    };

    const policyVersionsTableColumns = getTableColumns(config);

    return (
        <DeletableResourceTable
            data={formattedVersions}
            columns={policyVersionsTableColumns}
            resourceRef={resourceRef}
            searchOptions={{ column: "alias", label: "Alias" }}
            defaultSorting={[{ id: "last_updated_at", desc: true }]}
            CreationDialog={<CreateVersionDialog policyId={policy.policy_id} />}
            deleteOptions={deleteOptions}
        />
    );
}

function getTableColumns(config: PolicyVersionsTableConfig): ColumnDef<ExtendedPolicyVersion>[] {
    return [
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
                        <span className="mr-2">Alias</span>
                        <ArrowUpDown className="w-5 h-5" />
                    </Button>
                );
            },
            cell: ({ row }) => <div>{row.getValue("alias")}</div>,
        },
        {
            header: "Active",
            accessorKey: "activeStatus",
            cell: ({ row }) => {
                const status = row.getValue("activeStatus") as string;
                const variant =
                    ACTIVE_STATUS_VARIANT[status as keyof typeof ACTIVE_STATUS_VARIANT] ||
                    "outline";

                return <Badge variant={variant as any}>{status}</Badge>;
            },
        },
        {
            header: "Valid",
            accessorKey: "validationStatus",
            cell: ({ row }) => {
                const status = row.getValue("validationStatus") as WorkflowStatus;

                return (
                    <Badge variant={status === WorkflowStatus.Valid ? "default" : "destructive"}>
                        {status}
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
    ];
}

function getActiveVersions(policyData: Policy): string[] {
    if (policyData.allocation_strategy == null) {
        return [];
    }
    const choiceVersions = policyData.allocation_strategy.choice.map((opt) => {
        return opt.policy_version_id;
    });
    const shadowVersions = policyData.allocation_strategy.shadow || [];
    return [...choiceVersions, ...shadowVersions];
}

// Define interfaces for the policy version with status fields
interface ExtendedPolicyVersion extends PolicyVersion {
    validationStatus: WorkflowStatus;
    activeStatus: string;
}

// Define active status styles
const ACTIVE_STATUS_VARIANT = {
    active: "default",
    inactive: "outline",
};
