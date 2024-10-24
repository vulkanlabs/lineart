"use client";
import { formatDistanceStrict } from "date-fns";
import { usePathname, useRouter } from "next/navigation";

import { ShortenedID } from "@/components/shortened-id";

import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

export function RunsTable({ runs }) {
    const router = useRouter();
    const pathname = usePathname();

    return (
        <Table>
            <TableCaption>Runs</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Version ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Result</TableHead>
                    <TableHead>Created At</TableHead>
                    <TableHead>Duration</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {runs.map((run) => (
                    <TableRow
                        key={run.run_id}
                        className="cursor-pointer"
                        onClick={() => router.push(`${pathname}/${run.run_id}`)}
                    >
                        <TableCell>
                            <ShortenedID id={run.run_id} />
                        </TableCell>
                        <TableCell>
                            <ShortenedID id={run.policy_version_id} />
                        </TableCell>
                        <TableCell>
                            <RunStatus value={run.status} />
                        </TableCell>
                        <TableCell>
                            {run.result == null || run.result == "" ? "-" : run.result}
                        </TableCell>
                        <TableCell>{run.created_at}</TableCell>
                        <TableCell>
                            {formatDistanceStrict(run.last_updated_at, run.created_at)}
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

function RunStatus({ value }) {
    const getColor = (status) => {
        switch (status) {
            case "SUCCESS":
                return "bg-green-200";
            case "FAILURE":
                return "bg-red-200";
            default:
                return "bg-gray-200";
        }
    };

    return <p className={`w-fit p-[0.3em] rounded-lg ${getColor(value)}`}>{value}</p>;
}
