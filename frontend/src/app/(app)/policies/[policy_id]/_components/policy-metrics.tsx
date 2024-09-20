"use client";

import React, { useState, useEffect } from "react";
import { subDays } from "date-fns";

import { fetchRunsCount, fetchRunDurationStats, fetchRunDurationByStatus } from "@/lib/api";
import { DatePickerWithRange } from "@/components/charts/date-picker";
import {
    RunsChart,
    RunsByStatusChart,
    RunDurationStatsChart,
    AvgDurationByStatusChart,
} from "@/components/charts/policy-stats";

export default function PolicyMetrics({ policyId }: { policyId: string }) {
    const [runsCount, setRunsCount] = useState([]);
    const [runsByStatus, setRunsByStatus] = useState([]);
    const [runDurationStats, setRunDurationStats] = useState([]);
    const [runDurationByStatus, setRunDurationByStatus] = useState([]);
    const [dateRange, setDateRange] = useState({
        from: subDays(new Date(), 7),
        to: new Date(),
    });

    useEffect(() => {
        if (!dateRange || !dateRange.from || !dateRange.to) {
            return;
        }
        fetchRunsCount(policyId, dateRange.from, dateRange.to)
            .then((data) => setRunsCount(data))
            .catch((error) => {
                console.error(error);
            });

        fetchRunsCount(policyId, dateRange.from, dateRange.to, true)
            .then((data) => setRunsByStatus(data))
            .catch((error) => {
                console.error(error);
            });

        fetchRunDurationStats(policyId, dateRange.from, dateRange.to)
            .then((data) => setRunDurationStats(data))
            .catch((error) => {
                console.error(error);
            });

        fetchRunDurationByStatus(policyId, dateRange.from, dateRange.to)
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
    );
}

function EmptyChart() {
    return (
        <div className="flex items-center justify-center h-full w-full">
            <p className="text-sm font-semibold text-gray-500">Nenhuma execução registrada.</p>
        </div>
    );
}
