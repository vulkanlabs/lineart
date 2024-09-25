import { stackServerApp } from "@/stack";

import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { fetchPolicyRuns } from "@/lib/api";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const runs = await fetchPolicyRuns(user, params.policy_id).catch((error) => {
        console.error(error);
        return [];
    });

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div className="flex items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Execuções</h1>
            </div>
            <RunsTable runs={runs} />
        </div>
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

function RunsTable({ runs }) {
    return (
        <Table>
            <TableCaption>Execuções</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Versão</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Resultado</TableHead>
                    <TableHead>Criada Em</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {runs.map((run) => (
                    <TableRow key={run.run_id}>
                        <TableCell>{run.run_id}</TableCell>
                        <TableCell>{run.policy_version_id}</TableCell>
                        <TableCell>
                            <RunStatus value={run.status} />
                        </TableCell>
                        <TableCell>
                            {run.result == null || run.result == "" ? "-" : run.result}
                        </TableCell>
                        <TableCell>{run.created_at}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
