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
    const [dateRange, setDateRange] = useState({
        from: subDays(new Date(), 7),
        to: new Date(),
    });

    const refreshTime = 5000;
    const baseUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

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

    useEffect(() => {
        refreshPolicyVersions();
        const policiesInterval = setInterval(refreshPolicyVersions, refreshTime);
        return () => clearInterval(policiesInterval);
    }, []);

    useEffect(() => {
        if (!dateRange || !dateRange.from || !dateRange.to) {
            return;
        }
        const refreshRunsCount = () =>
            fetchRunsCount(baseUrl, params.policy_id, dateRange.from, dateRange.to)
                .then((data) => setRunsCount(data))
                .catch((error) => {
                    console.error(error);
                });
        refreshRunsCount();
        const runsInterval = setInterval(refreshRunsCount, refreshTime);
        return () => clearInterval(runsInterval);
    }, [dateRange]);

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div>
                <h1 className="text-lg font-semibold md:text-2xl">Versões</h1>
                <PolicyVersionsTable policyVersions={policyVersions} />
            </div>
            <div >
                <h1 className="text-lg font-semibold md:text-2xl">Métricas</h1>
                <h3 className="font-semibold md:text-xl">Quantidade de Execuções</h3>
                <div className="absolute h-3/5 w-3/4 mt-4">
                    <div className="float-end">
                        <DatePickerWithRange date={dateRange} setDate={setDateRange} />
                    </div>
                    <RunsChart chartData={runsCount} />
                </div>
            </div>
        </div >
    );
}


function PolicyVersionStatus({ value }) {
    if (value === "ativa") {
        return (
            <p className={`w-fit p-[0.3em] rounded-lg bg-green-200`}>
                {value}
            </p>
        );
    }
    return (
        <p className={`w-fit p-[0.3em] rounded-lg bg-gray-200`}>
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
        return (
            <div className="flex items-center justify-center h-full w-full">
                <p className="text-lg font-semibold text-gray-500">Nenhuma execução registrada.</p>
            </div>
        );
    }

    const chartConfig = {
        count: {
            label: "Execuções",
            color: "#2563eb",
        },
    };

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