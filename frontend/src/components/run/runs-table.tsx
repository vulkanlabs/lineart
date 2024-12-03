"use client";
import { formatDistanceStrict } from "date-fns";
import { usePathname, useRouter } from "next/navigation";

import { ShortenedID } from "@/components/shortened-id";
import { RefreshButton } from "../refresh-button";

import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

type RunData = {
    run_id: string;
    policy_version_id: string;
    status: string;
    result: string;
    created_at: string;
    last_updated_at: string;
};

type RunsTableProps = {
    runs: RunData[];
    policyVersionId?: string;
};

export function RunsTableComponent({ runs }: RunsTableProps) {
    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div className="flex justify-between items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Runs</h1>
                <RefreshButton />
            </div>
            <div className="mt-4 max-h-[75vh] overflow-scroll">
                <RunsTable runs={runs} />
            </div>
        </div>
    );
}

function RunsTable({ runs }: { runs: RunData[] }) {
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
