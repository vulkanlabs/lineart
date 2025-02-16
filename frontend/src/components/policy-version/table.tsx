"use client";
import { DetailsButton } from "@/components/details-button";

import { DataTable } from "@/components/data-table";
import { ShortenedID } from "@/components/shortened-id";
import { parseDate } from "@/lib/utils";
import { ColumnDef } from "@tanstack/react-table";
import { VersionStatus } from "@/components/policy-version/status";
import { Policy } from "@vulkan-server/Policy";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";

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
        header: "Status",
        accessorKey: "status",
        cell: ({ row }) => <VersionStatus value={row.getValue("status")} />,
    },
    {
        header: "Created At",
        accessorKey: "created_at",
        cell: ({ row }) => parseDate(row.getValue("created_at")),
    },
];

export function PolicyVersionsTable({
    policy,
    policyVersions,
}: {
    policy: Policy;
    policyVersions: PolicyVersion[];
}) {
    const formattedVersions = policyVersions.map((policyVersion) => {
        const status =
            policyVersion.policy_version_id === policy.active_policy_version_id
                ? "active"
                : "inactive";
        return {
            ...policyVersion,
            status: status,
        };
    });

    return <DataTable columns={PolicyVersionsTableColumns} data={formattedVersions} />;
}
