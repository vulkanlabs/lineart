"use client";

import { useRouter } from "next/navigation";

import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

export default function PolicyVersionsTable({ policyVersions }: { policyVersions: any[] }) {
    const router = useRouter();

    function goToVersion(policyVersion: any) {
        const version = policyVersion.policy_version_id;
        router.push(`/policyVersions/${version}/workflow`);
    }

    return (
        <div>
            <h1 className="text-lg font-semibold md:text-2xl">Versions</h1>
            <Table>
                <TableCaption>Available versions.</TableCaption>
                <TableHeader>
                    <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Tag</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Created At</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {policyVersions.map((policyVersion) => (
                        <TableRow
                            key={policyVersion.policy_version_id}
                            className="cursor-pointer"
                            onClick={() => goToVersion(policyVersion)}
                        >
                            <TableCell>{policyVersion.policy_version_id}</TableCell>
                            <TableCell>{policyVersion.alias}</TableCell>
                            <TableCell>
                                <VersionStatus value={policyVersion.status} />
                            </TableCell>
                            <TableCell>{policyVersion.created_at}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
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
