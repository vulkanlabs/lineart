"use client";

// React and Next.js
import React, { useState, useEffect, useRef } from "react";

// External libraries
import { DateRange } from "react-day-picker";
import { subDays } from "date-fns";

// Vulkan packages
import {
    AvgDurationByStatusChart,
    DatePickerWithRange,
    RunDurationStatsChart,
    RunErrorRateChart,
    RunOutcomeDistributionChart,
    RunOutcomesChart,
    RunsChart,
    VersionPicker,
} from "../../index";
import { PolicyVersion } from "@vulkanlabs/client-open";

export interface PolicyMetricsConfig {
    projectId?: string;
    metricsLoader: (params: {
        policyId: string;
        dateRange: DateRange;
        versions: string[];
        projectId?: string;
    }) => Promise<{
        runsCount: any[];
        errorRate: any[];
        runDurationStats: any[];
        runDurationByStatus: any[];
    }>;
    outcomesLoader: (
        policyId: string,
        data: { dateRange: DateRange; versions: string[] },
        projectId?: string,
    ) => Promise<any[]>;
}

export function PolicyMetrics({
    policyId,
    config,
    versions,
}: {
    policyId: string;
    config: PolicyMetricsConfig;
    versions: PolicyVersion[];
}) {
    // Chart Data
    const [outcomeDistribution, setOutcomeDistribution] = useState<any[]>([]);
    const [runsCount, setRunsCount] = useState<any[]>([]);
    const [errorRate, setErrorRate] = useState<any[]>([]);
    const [runDurationStats, setRunDurationStats] = useState<any[]>([]);
    const [runDurationByStatus, setRunDurationByStatus] = useState<any[]>([]);

    // Filters & Interactions
    const [dateRange, setDateRange] = useState<DateRange>({
        from: subDays(new Date(), 7),
        to: new Date(),
    });
    const [selectedVersions, setSelectedVersions] = useState(
        versions.map((v) => v.policy_version_id),
    );

    // Track if we're already loading to prevent duplicate calls
    const isLoadingRef = useRef(false);

    useEffect(() => {
        if (!dateRange || !dateRange.from || !dateRange.to) {
            return;
        }

        // Prevent duplicate calls
        if (isLoadingRef.current) {
            return;
        }

        isLoadingRef.current = true;

        const metricsPromise = config.metricsLoader({
            policyId,
            dateRange,
            versions: selectedVersions,
            projectId: config.projectId,
        });

        const outcomesPromise = config.outcomesLoader(
            policyId,
            { dateRange, versions: selectedVersions },
            config.projectId,
        );

        Promise.all([metricsPromise, outcomesPromise])
            .then(([metricsData, outcomesData]) => {
                setRunsCount(metricsData.runsCount);
                setErrorRate(metricsData.errorRate);
                setRunDurationStats(metricsData.runDurationStats);
                setRunDurationByStatus(metricsData.runDurationByStatus);
                setOutcomeDistribution(outcomesData);
            })
            .catch((error: any) => {
                console.error("Error loading metrics:", error);
            })
            .finally(() => {
                isLoadingRef.current = false;
            });
    }, [dateRange, selectedVersions, config.projectId]);

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
            component: RunErrorRateChart,
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
        <div className="overflow-hidden flex flex-col gap-4">
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
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 w-full px-4 lg:px-8">
                {graphDefinitions.map((graphDefinition) => (
                    <div key={graphDefinition.name} className="col-span-1 px-2 lg:px-4 pb-8">
                        <h3 className="text-lg">{graphDefinition.name}</h3>
                        <div>
                            <graphDefinition.component chartData={graphDefinition.data} />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
