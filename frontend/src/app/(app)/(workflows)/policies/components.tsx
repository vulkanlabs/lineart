"use client";

import { useRouter } from "next/navigation";

import { DataTable } from "@/components/data-table";
import { DetailsButton } from "@/components/details-button";
import { ShortenedID } from "@/components/shortened-id";
import { Button } from "@/components/ui/button";
import { parseDate } from "@/lib/utils";
import { ColumnDef } from "@tanstack/react-table";
import { Policy } from "@vulkan-server/Policy";

export default function PoliciesPage({ policies }: { policies: any[] }) {
    const router = useRouter();

    return (
        <div>
            <Button onClick={() => router.refresh()}>Refresh</Button>
            <div className="my-4">
                <DataTable
                    columns={PolicyTableColumns}
                    data={policies}
                    emptyMessage="You don't have any policies yet."
                />
            </div>
        </div>
    );
}

const PolicyTableColumns: ColumnDef<Policy>[] = [
    {
        accessorKey: "link",
        header: "",
        cell: ({ row }) => (
            <DetailsButton href={`/policies/${row.getValue("policy_id")}/versions`} />
        ),
    },
    {
        header: "ID",
        accessorKey: "policy_id",
        cell: ({ row }) => <ShortenedID id={row.getValue("policy_id")} />,
    },
    { header: "Name", accessorKey: "name" },
    {
        header: "Description",
        accessorKey: "description",
        cell: ({ row }) => row.getValue("description") || "-",
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
        header: "Last Updated At",
        accessorKey: "last_updated_at",
        cell: ({ row }) => parseDate(row.getValue("last_updated_at")),
    },
];
