"use client";
import { DetailsButton } from "@/components/details-button";

import { DataTable } from "@/components/data-table";
import { ShortenedID } from "@/components/shortened-id";
import { parseDate } from "@/lib/utils";
import { ColumnDef } from "@tanstack/react-table";
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

export default function PolicyVersionsTable({ policyVersions }: { policyVersions: any[] }) {
    return <DataTable columns={PolicyVersionsTableColumns} data={policyVersions} />;
}

function VersionStatus({ value }) {
    const getColor = (status: string) => {
        switch (status) {
            case "active":
                return "bg-green-200";
            case "inactive":
                return "bg-gray-200";
            default:
                return "bg-gray-200";
        }
    };

    return <p className={`w-fit p-[0.3em] rounded-lg ${getColor(value)}`}>{value}</p>;
}
