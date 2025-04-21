"use client";

import { ColumnDef } from "@tanstack/react-table";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { Policy } from "@vulkan-server/Policy";

import { DetailsButton } from "@/components/details-button";
import { DataTable } from "@/components/data-table";
import { ShortenedID } from "@/components/shortened-id";
import { RefreshButton } from "@/components/refresh-button";
import { parseDate } from "@/lib/utils";

export function AllocatedVersionsTable({
    policy,
    policyVersions,
}: {
    policy: Policy;
    policyVersions: PolicyVersion[];
}) {
    const formattedVersions = formatVersions({ policy, policyVersions });
    return (
        <div>
            <div className="flex gap-4">
                <RefreshButton />
                {/* <UpdateAllocationsDialog policyVersions={policyVersions} /> */}
            </div>
            <div className="my-4">
                <DataTable
                    columns={PolicyVersionsTableColumns}
                    data={formattedVersions}
                    emptyMessage="You don't have any allocated versions yet."
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
    if (policyVersions.length === 0) {
        return [];
    }
    const spec = getAllocationSpec(policy.allocation_strategy);
    const formattedVersions = policyVersions.map((policyVersion) => {
        return {
            ...policyVersion,
            mode: spec[policyVersion.policy_version_id].mode,
            frequency: spec[policyVersion.policy_version_id].frequency,
        };
    });
    return formattedVersions;
}

function getAllocationSpec(strategy) {
    const choiceVersions = strategy.choice.reduce((result, version) => {
        result[version.policy_version_id] = { mode: "choice", frequency: version.frequency };
        return result;
    }, {});
    const shadowVersions = strategy.shadow.reduce((result, version_id) => {
        result[version_id] = { mode: "shadow", frequency: null };
        return result;
    }, {});
    return { ...choiceVersions, ...shadowVersions };
}

const PolicyVersionsTableColumns: ColumnDef<PolicyVersion>[] = [
    {
        header: "",
        accessorKey: "link",
        cell: ({ row }) => (
            <DetailsButton href={`/policyVersions/${row.getValue("policy_version_id")}/workflow`} />
        ),
    },
    {
        header: "ID",
        accessorKey: "policy_version_id",
        cell: ({ row }) => <ShortenedID id={row.getValue("policy_version_id")} />,
    },
    { header: "Tag", accessorKey: "alias" },
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
        cell: ({ row }) => parseDate(row.getValue("created_at")),
    },
];

function parseFrequency(frequency: number) {
    if (frequency === null) {
        return "N/A";
    }
    return frequency / 10 + "%";
}

function VersionStatus({ value }) {
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
