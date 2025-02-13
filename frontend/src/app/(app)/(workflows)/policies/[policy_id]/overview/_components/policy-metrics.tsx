"use client";

import React, { useState, useEffect } from "react";
import { subDays } from "date-fns";

import { DatePickerWithRange } from "@/components/charts/date-picker";
import { VersionPicker } from "@/components/charts/version-picker";
import {
    RunsChart,
    ErrorRateChart,
    RunDurationStatsChart,
    AvgDurationByStatusChart,
    RunOutcomesChart,
    RunOutcomeDistributionChart,
} from "@/components/charts/policy-stats";
import { EmptyChart } from "@/components/charts/empty";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";

export default function PolicyMetrics({
    policyId,
    metricsLoader,
    outcomesLoader,
    versions,
}: {
    policyId: string;
    metricsLoader: any;
    outcomesLoader: (params: {
        policyId: string;
        dateRange: { from: Date; to: Date };
        versions: string[];
    }) => Promise<{ runOutcomes: any[] }>;
    versions: PolicyVersion[];
}) {
    // Chart Data
    const [outcomeDistribution, setOutcomeDistribution] = useState([]);
    const [runsCount, setRunsCount] = useState([]);
    const [errorRate, setErrorRate] = useState([]);
    const [runDurationStats, setRunDurationStats] = useState([]);
    const [runDurationByStatus, setRunDurationByStatus] = useState([]);
    // Filters & Interactions
    const [dateRange, setDateRange] = useState({
        from: subDays(new Date(), 7),
        to: new Date(),
    });
    const [selectedVersions, setSelectedVersions] = useState(
        versions.map((v) => v.policy_version_id),
    );

    useEffect(() => {
        if (!dateRange || !dateRange.from || !dateRange.to) {
            return;
        }
        metricsLoader({ policyId, dateRange, versions: selectedVersions })
            .then((data) => {
                setRunsCount(data.runsCount);
                setErrorRate(data.errorRate);
                setRunDurationStats(data.runDurationStats);
                setRunDurationByStatus(data.runDurationByStatus);
            })
            .catch((error) => {
                console.error(error);
            });

        outcomesLoader({ policyId, dateRange, versions: selectedVersions })
            .then((data) => {
                setOutcomeDistribution(data.runOutcomes);
            })
            .catch((error) => {
                console.error(error);
            });
    }, [dateRange, selectedVersions]);

    const graphDefinitions = [
        {
            name: "Policy Outcomes",
            data: outcomeDistribution,
            component: RunOutcomesChart,
        },
        {
            name: "Policy Outcome Distribution (%)",
            data: outcomeDistribution,
            component: RunOutcomeDistributionChart,
        },
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
        <div className="overflow-scroll flex flex-col gap-4">
            <div className="flex flex-col gap-4 pb-4">
                <h1 className="text-lg font-semibold md:text-2xl">Metrics</h1>
                <div className="flex gap-4">
                    <DatePickerWithRange date={dateRange} setDate={setDateRange} />
                    <VersionPicker
                        versions={versions}
                        selectedVersions={selectedVersions}
                        setSelectedVersions={setSelectedVersions}
                    />
                </div>
            </div>
            <div className="grid grid-cols-2 gap-4 w-[90%] px-16 overflow-y-scroll">
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
