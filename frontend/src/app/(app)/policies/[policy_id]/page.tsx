"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from 'next/navigation';
import { Bar, BarChart, XAxis, YAxis } from "recharts";
import { subDays } from "date-fns";

import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { fetchPolicy, fetchPolicyVersions, fetchRunsCount } from "@/lib/api";

import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegend,
    ChartLegendContent,
} from "@/components/ui/chart";

import { DatePickerWithRange } from "@/components/date-picker";

export default function Page({ params }) {
    const [policyVersions, setPolicyVersions] = useState([]);
    const [runsCount, setRunsCount] = useState([]);
    const [runsByStatus, setRunsByStatus] = useState([]);
    const [dateRange, setDateRange] = useState({
        from: subDays(new Date(), 7),
        to: new Date(),
    });

    const refreshTime = 15000;
    const baseUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

    useEffect(() => {
        const refreshPolicyVersions = async () => {
            try {
                const policyData = await fetchPolicy(baseUrl, params.policy_id);
                const policyVersionsData = await fetchPolicyVersions(baseUrl, params.policy_id);

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
        fetchRunsCount(baseUrl, params.policy_id, dateRange.from, dateRange.to)
            .then((data) => setRunsCount(data))
            .catch((error) => {
                console.error(error);
            });


        fetchRunsCount(baseUrl, params.policy_id, dateRange.from, dateRange.to, true)
            .then((data) => setRunsByStatus(data))
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
        // {
        //     name: "Duração Média",
        //     data: runsCount,
        //     component: RunsChart,
        // },
        // {
        //     name: "Distribuição de Resultados",
        //     data: runsCount,
        //     component: RunsByStatusChart,
        // },
    ];

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div>
                <h1 className="text-lg font-semibold md:text-2xl">Versões</h1>
                <PolicyVersionsTable policyVersions={policyVersions} />
            </div>
            <div >
                <div className="flex gap-4 pb-4">
                    <h1 className="text-lg font-semibold md:text-2xl">Métricas</h1>
                    <div>
                        <DatePickerWithRange date={dateRange} setDate={setDateRange} />
                    </div>
                </div>
                {/* Note: This is ugly, but not defining height or using h-full
                          causes the graph to not render. */}
                <div className="flex h-3/4 w-3/4">
                    <div className="grid grid-cols-2 flex-shrink gap-4">
                        {graphDefinitions.map((graphDefinition) => (
                            <div key={graphDefinition.name} className="h-full min-w-full">
                                <h3 className="text-lg">{graphDefinition.name}</h3>
                                <graphDefinition.component chartData={graphDefinition.data} />
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div >
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

    return (
        <p className={`w-fit p-[0.3em] rounded-lg ${getColor(value)}`}>
            {value}
        </p>
    );
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
                        <TableCell><PolicyVersionStatus value={policyVersion.status} /></TableCell>
                        <TableCell>{policyVersion.created_at}</TableCell>
                    </TableRow>

                ))}
            </TableBody>
        </Table >
    );
}

function RunsChart({ chartData }) {
    if (chartData.length === 0) {
        return EmptyChart();
    }

    const chartConfig = {
        count: {
            label: "Execuções",
            color: "#2563eb",
        },
    } satisfies ChartConfig;

    return (
        <ChartContainer config={chartConfig} className="h-full w-full" >
            <BarChart accessibilityLayer data={chartData}>
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    axisLine={false}
                />
                <YAxis
                    type="number"
                    domain={[0, dataMax => Math.ceil(dataMax / 10) * 10]}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Bar dataKey="count" fill="var(--color-count)" radius={4} />
            </BarChart>
        </ChartContainer>
    );
}


function RunsByStatusChart({ chartData }) {
    console.log("chartData", chartData);
    if (chartData.length === 0) {
        return EmptyChart();
    }

    const chartConfig = {
        SUCCESS: {
            label: "Success",
            color: "hsl(var(--chart-1))",
        },
        FAILURE: {
            label: "Failure",
            color: "hsl(var(--chart-2))",
        },
        STARTED: {
            label: "Started",
            color: "hsl(var(--chart-3))",
        },
        PENDING: {
            label: "Pending",
            color: "hsl(var(--chart-4))",
        },
    } satisfies ChartConfig


    return (
        <ChartContainer config={chartConfig} className="h-full w-full" >
            <BarChart accessibilityLayer data={chartData}>
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    axisLine={false}
                />
                <YAxis
                    type="number"
                    domain={[0, dataMax => Math.ceil(dataMax / 10) * 10]}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Bar dataKey="SUCCESS" radius={0} stackId="a" fill="var(--color-SUCCESS)" />
                <Bar dataKey="FAILURE" radius={0} stackId="a" fill="var(--color-FAILURE)" />
                <Bar dataKey="STARTED" radius={0} stackId="a" fill="var(--color-STARTED)" />
                <Bar dataKey="PENDING" radius={0} stackId="a" fill="var(--color-PENDING)" />
            </BarChart>
        </ChartContainer>
    );
}

function RunDurationChart({ chartData }) {
    if (chartData.length === 0) {
        return EmptyChart();
    }

    const chartConfig = {
        count: {
            label: "Execuções",
            color: "#2563eb",
        },
    } satisfies ChartConfig;

    return (
        <ChartContainer config={chartConfig} className="h-full w-full" >
            <BarChart accessibilityLayer data={chartData}>
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    tickMargin={10}
                    axisLine={false}
                />
                <YAxis
                    type="number"
                    domain={[0, dataMax => Math.ceil(dataMax / 10) * 10]}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Bar dataKey="count" fill="var(--color-count)" radius={4} />
            </BarChart>
        </ChartContainer>
    );
}

function EmptyChart() {
    return (
        <div className="flex items-center justify-center h-full w-full">
            <p className="text-lg font-semibold text-gray-500">Nenhuma execução registrada.</p>
        </div>
    );
}