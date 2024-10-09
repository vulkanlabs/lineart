import { stackServerApp } from "@/stack";
import { Suspense } from "react";

import { InnerNavbarSectionProps, InnerNavbar } from "@/components/inner-navbar";
import { fetchPolicyVersion, fetchRun, fetchRunsData, fetchRunLogs } from "@/lib/api";
import Loader from "@/components/loader";

import WorkflowPage from "./components/workflow";

type Event = {
    log_type?: string;
    message: string;
    level: string;
};

type Log = {
    timestamp: string;
    step_key?: string;
    source: string;
    event: Event;
};

type RunLogs = {
    run_id: string;
    status: string;
    last_updated_at: string;
    logs: Log[];
};

export default async function Page({ params }) {
    const innerNavbarSections: InnerNavbarSectionProps[] = [{ key: "Run:", value: params.run_id }];

    return (
        <div className="flex flex-col w-full h-full overflow-scroll">
            <InnerNavbar sections={innerNavbarSections} />
            <div className="grid grid-rows-2 h-full w-full overflow-scroll">
                <div className="row-span-1 w-full border-b-2">
                    <Suspense fallback={<Loader />}>
                        <WorkflowSection runId={params.run_id} />
                    </Suspense>
                </div>
                <div className="row-span-1 w-full">
                    <Suspense fallback={<Loader />}>
                        <LogsTable runId={params.run_id} />
                    </Suspense>
                </div>
            </div>
        </div>
    );
}

async function WorkflowSection({ runId }) {
    const user = await stackServerApp.getUser();
    const runsData = await fetchRunsData(user, runId).catch((error) => {
        console.error(error);
        return {};
    });
    const run = await fetchRun(user, runId).catch((error) => {
        console.error(error);
        return {};
    });
    const policyVersion = await fetchPolicyVersion(user, run.policy_version_id).catch((error) => {
        console.error(error);
    });
    const graphData = JSON.parse(policyVersion.graph_definition);

    return <WorkflowPage graphData={graphData} runsData={runsData} />;
}

async function LogsTable({ runId }) {
    const user = await stackServerApp.getUser();
    const runLogs: RunLogs = await fetchRunLogs(user, runId).catch((error) => {
        console.error(error);
        return {};
    });

    return (
        <div className="flex flex-row w-full h-full overflow-scroll">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <TableHeader>Timestamp</TableHeader>
                        <TableHeader>Step Key</TableHeader>
                        <TableHeader>Source</TableHeader>
                        <TableHeader>Log Type</TableHeader>
                        <TableHeader>Message</TableHeader>
                        <TableHeader>Level</TableHeader>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {runLogs.logs.map((log, index) => (
                        <tr key={index}>
                            <TableCell>{log.timestamp}</TableCell>
                            <TableCell>{log.step_key || "N/A"}</TableCell>
                            <TableCell>{log.source}</TableCell>
                            <TableCell>{log.event.log_type || "N/A"}</TableCell>
                            <TableCell>{log.event.message}</TableCell>
                            <TableCell>{log.event.level}</TableCell>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function TableHeader({ children }) {
    return (
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            {children}
        </th>
    );
}

function TableCell({ children }) {
    return <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">{children}</td>;
}
