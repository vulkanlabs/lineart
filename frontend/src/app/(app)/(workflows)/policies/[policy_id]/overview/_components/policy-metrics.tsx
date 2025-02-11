"use client";

import React, { useState, useEffect } from "react";
import { subDays } from "date-fns";

import { DatePickerWithRange } from "@/components/charts/date-picker";
import {
    RunsChart,
    ErrorRateChart,
    RunDurationStatsChart,
    AvgDurationByStatusChart,
} from "@/components/charts/policy-stats";

export default function PolicyMetrics({
    policyId,
    dataLoader,
}: {
    policyId: string;
    dataLoader: any;
}) {
    const [runsCount, setRunsCount] = useState([]);
    const [errorRate, setErrorRate] = useState([]);
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
        dataLoader({ policyId, dateRange })
            .then((data) => {
                setRunsCount(data.runsCount);
                setErrorRate(data.errorRate);
                setRunDurationStats(data.runDurationStats);
                setRunDurationByStatus(data.runDurationByStatus);
            })
            .catch((error) => {
                console.error(error);
            });
    }, [dateRange]);

    const graphDefinitions = [
        {
            name: "Runs",
            data: runsCount,
            component: RunsChart,
        },
        {
            name: "Error Rate (%)",
            data: errorRate,
            component: ErrorRateChart,
        },
        {
            name: "Duration (seconds)",
            data: runDurationStats,
            component: RunDurationStatsChart,
        },
        {
            name: "Average Duration by Status (seconds)",
            data: runDurationByStatus,
            component: AvgDurationByStatusChart,
        },
    ];

    return (
        <div className="overflow-scroll">
            <div className="flex gap-4 pb-4">
                <h1 className="text-lg font-semibold md:text-2xl">Metrics</h1>
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
                            <div>
                                <graphDefinition.component chartData={graphDefinition.data} />
                            </div>
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
            <p className="text-sm font-semibold text-gray-500">No runs found.</p>
        </div>
    );
}
