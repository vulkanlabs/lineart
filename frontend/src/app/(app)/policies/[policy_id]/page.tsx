"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { subDays } from "date-fns";
import { useUser } from "@stackframe/stack";

import {
    fetchPolicy,
    fetchPolicyVersions,
    fetchRunsCount,
    fetchRunDurationStats,
    fetchRunDurationByStatus,
} from "@/lib/api";
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { DatePickerWithRange } from "@/components/charts/date-picker";
import {
    RunsChart,
    RunsByStatusChart,
    RunDurationStatsChart,
    AvgDurationByStatusChart,
} from "@/components/charts/policy-stats";

export default function Page({ params }) {
    const [policyVersions, setPolicyVersions] = useState([]);
    const [runsCount, setRunsCount] = useState([]);
    const [runsByStatus, setRunsByStatus] = useState([]);
    const [runDurationStats, setRunDurationStats] = useState([]);
    const [runDurationByStatus, setRunDurationByStatus] = useState([]);
    const [dateRange, setDateRange] = useState({
        from: subDays(new Date(), 7),
        to: new Date(),
    });
    const user = useUser();
    const refreshTime = 15000;

    useEffect(() => {
        const refreshPolicyVersions = async () => {
            try {
                const policyData = await fetchPolicy(user, params.policy_id);
                const policyVersionsData = await fetchPolicyVersions(user, params.policy_id);

                policyVersionsData.forEach((policyVersion) => {
                    if (policyVersion.policy_version_id === policyData.active_policy_version_id) {
                        policyVersion.status = "ativa";
                    } else {
                        policyVersion.status = "inativa";
                    }
                });
                setPolicyVersions(policyVersionsData);
            } catch (error) {
                console.error(error);
            }
        };
        refreshPolicyVersions();
        const policiesInterval = setInterval(refreshPolicyVersions, refreshTime);
        return () => clearInterval(policiesInterval);
    }, []);

    useEffect(() => {
        if (!dateRange || !dateRange.from || !dateRange.to) {
            return;
        }
        fetchRunsCount(params.policy_id, dateRange.from, dateRange.to)
            .then((data) => setRunsCount(data))
            .catch((error) => {
                console.error(error);
            });

        fetchRunsCount(params.policy_id, dateRange.from, dateRange.to, true)
            .then((data) => setRunsByStatus(data))
            .catch((error) => {
                console.error(error);
            });

        fetchRunDurationStats(params.policy_id, dateRange.from, dateRange.to)
            .then((data) => setRunDurationStats(data))
            .catch((error) => {
                console.error(error);
            });

        fetchRunDurationByStatus(params.policy_id, dateRange.from, dateRange.to)
            .then((data) => setRunDurationByStatus(data))
            .catch((error) => {
                console.error(error);
            });
    }, [dateRange]);

    const graphDefinitions = [
        {
            name: "Execuções",
            data: runsCount,
            component: RunsChart,
        },
        {
            name: "Execuções por Status",
            data: runsByStatus,
            component: RunsByStatusChart,
        },
        {
            name: "Duração (segundos)",
            data: runDurationStats,
            component: RunDurationStatsChart,
        },
        {
            name: "Duração Média por Status (segundos)",
            data: runDurationByStatus,
            component: AvgDurationByStatusChart,
        },
    ];

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div>
                <h1 className="text-lg font-semibold md:text-2xl">Versões</h1>
                <PolicyVersionsTable policyVersions={policyVersions} />
            </div>
            <div>
                <div className="flex gap-4 pb-4">
                    <h1 className="text-lg font-semibold md:text-2xl">Métricas</h1>
                    <div>
                        <DatePickerWithRange date={dateRange} setDate={setDateRange} />
                    </div>
                </div>
                {/* Note: This is ugly, but not defining height or using h-full
                          causes the graph to not render. */}
                <div className="grid grid-cols-2 gap-4 w-[85%] px-16 overflow-y-scroll">
                    {graphDefinitions.map((graphDefinition) => (
                        <div key={graphDefinition.name} className="col-span-1 px-8 pb-8">
                            <h3 className="text-lg">{graphDefinition.name}</h3>
                            {graphDefinition.data.length === 0 ? (
                                <EmptyChart />
                            ) : (
                                <graphDefinition.component chartData={graphDefinition.data} />
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function PolicyVersionStatus({ value }) {
    const getColor = (status: string) => {
        switch (status) {
            case "ativa":
                return "bg-green-200";
            case "inativa":
                return "bg-gray-200";
            default:
                return "bg-gray-200";
        }
    };

    return <p className={`w-fit p-[0.3em] rounded-lg ${getColor(value)}`}>{value}</p>;
}

function PolicyVersionsTable({ policyVersions }) {
    const router = useRouter();

    return (
        <Table>
            <TableCaption>Versões disponíveis.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Tag</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Criada Em</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {policyVersions.map((policyVersion) => (
                    <TableRow
                        key={policyVersion.policy_version_id}
                        className="cursor-pointer"
                        onClick={() => router.push(`/policies/${policyVersion.policy_id}/workflow`)}
                    >
                        <TableCell>{policyVersion.policy_version_id}</TableCell>
                        <TableCell>{policyVersion.alias}</TableCell>
                        <TableCell>
                            <PolicyVersionStatus value={policyVersion.status} />
                        </TableCell>
                        <TableCell>{policyVersion.created_at}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

function EmptyChart() {
    return (
        <div className="flex items-center justify-center h-full w-full">
            <p className="text-sm font-semibold text-gray-500">Nenhuma execução registrada.</p>
        </div>
    );
}
