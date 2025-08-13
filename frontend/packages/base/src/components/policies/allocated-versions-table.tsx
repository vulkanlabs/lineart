"use client";

// External libraries
import { ColumnDef } from "@tanstack/react-table";

// Vulkan packages
import { DetailsButton, DataTable, ShortenedID, RefreshButton } from "@vulkanlabs/base";
import type { Policy, PolicyVersion, PolicyAllocationStrategy } from "@vulkanlabs/client-open";

export interface AllocatedVersionsTableConfig {
    parseDate: (date: string) => string;
    UpdateAllocationsDialog: React.ComponentType<{
        policyId: string;
        currentAllocation: PolicyAllocationStrategy | null;
        policyVersions: PolicyVersion[];
    }>;
}

export function SharedAllocatedVersionsTable({
    policy,
    policyVersions,
    allocatedAndShadowVersions,
    config,
}: {
    policy: Policy;
    policyVersions: PolicyVersion[];
    allocatedAndShadowVersions: PolicyVersion[];
    config: AllocatedVersionsTableConfig;
}) {
    const formattedVersions = formatVersions({
        policy,
        policyVersions: allocatedAndShadowVersions,
    });
    return (
        <div>
            <div className="flex gap-4 my-4">
                <RefreshButton />
                <config.UpdateAllocationsDialog
                    policyId={policy.policy_id}
                    currentAllocation={
                        policy.allocation_strategy as PolicyAllocationStrategy | null
                    }
                    policyVersions={policyVersions}
                />
            </div>
            <div className="my-4">
                <DataTable
                    columns={getPolicyVersionsTableColumns(config)}
                    data={formattedVersions}
                    emptyMessage="No versions are currently allocated. Update the allocation strategy to add versions."
                />
            </div>
        </div>
    );
}

function formatVersions({
    policy,
    policyVersions,
}: {
    policy: Policy;
    policyVersions: PolicyVersion[];
}) {
    if (policyVersions.length === 0 || !policy.allocation_strategy) {
        return [];
    }
    const spec = getAllocationSpec(policy.allocation_strategy as PolicyAllocationStrategy);
    const formatted = policyVersions
        .map((policyVersion) => {
            const versionSpec = spec[policyVersion.policy_version_id];
            if (!versionSpec) return null; // Should not happen if policyVersions are derived from allocation_strategy
            return {
                ...policyVersion,
                mode: versionSpec.mode,
                frequency: versionSpec.frequency,
            };
        })
        .filter(Boolean); // Remove any nulls if a version in allocation_strategy was not found in policyVersions list
    return formatted as (PolicyVersion & { mode: string; frequency: number | null })[];
}

function getAllocationSpec(strategy: PolicyAllocationStrategy | null) {
    if (!strategy) return {};

    const spec: { [key: string]: { mode: string; frequency: number | null } } = {};

    strategy.choice.forEach((version) => {
        spec[version.policy_version_id] = { mode: "choice", frequency: version.frequency };
    });

    if (strategy.shadow) {
        strategy.shadow.forEach((version_id) => {
            // If a version is both in choice and shadow, 'choice' mode takes precedence for display clarity
            if (!spec[version_id]) {
                spec[version_id] = { mode: "shadow", frequency: null };
            }
        });
    }
    return spec;
}

function getPolicyVersionsTableColumns(
    config: AllocatedVersionsTableConfig
): ColumnDef<PolicyVersion & { mode: string; frequency: number | null }>[] {
    return [
        {
            header: "",
            accessorKey: "link",
            cell: ({ row }) => (
                <DetailsButton href={`/policyVersions/${row.original.policy_version_id}/workflow`} />
            ),
        },
        {
            header: "Version ID",
            accessorKey: "policy_version_id",
            cell: ({ row }) => <ShortenedID id={row.getValue("policy_version_id")} />,
        },
        { header: "Alias", accessorKey: "alias", cell: ({ row }) => row.getValue("alias") || "-" },
        {
            header: "Mode",
            accessorKey: "mode",
            cell: ({ row }) => <VersionStatus value={row.getValue("mode")} />,
        },
        {
            header: "Frequency",
            accessorKey: "frequency",
            cell: ({ row }) => parseFrequency(row.getValue("frequency")),
        },
        {
            header: "Created At",
            accessorKey: "created_at",
            cell: ({ row }) => config.parseDate(row.getValue("created_at")),
        },
    ];
}

function parseFrequency(frequency: number) {
    if (frequency === null) {
        return "N/A";
    }
    return frequency / 10 + "%";
}

function VersionStatus({ value }: { value: string }) {
    const getColor = (mode: string) => {
        switch (mode) {
            case "choice":
                return "bg-blue-200";
            case "shadow":
                return "bg-gray-200";
            default:
                return "bg-gray-200";
        }
    };

    return <p className={`w-fit p-[0.3em] rounded-lg ${getColor(value)}`}>{value}</p>;
}