"use server";

import {
    fetchRunsCount,
    fetchRunDurationStats,
    fetchRunDurationByStatus,
    fetchRunOutcomes,
} from "@/lib/api";

export async function fetchMetricsData({ policyId, dateRange, versions }) {
    const runsCount = await fetchRunsCount(policyId, dateRange.from, dateRange.to, versions).catch(
        (error) => {
            console.error(error);
        },
    );

    const runDurationStats = await fetchRunDurationStats(
        policyId,
        dateRange.from,
        dateRange.to,
        versions,
    ).catch((error) => {
        console.error(error);
    });

    const runDurationByStatus = await fetchRunDurationByStatus(
        policyId,
        dateRange.from,
        dateRange.to,
        versions,
    ).catch((error) => {
        console.error(error);
    });

    return { runsCount, errorRate: runsCount, runDurationStats, runDurationByStatus };
}

export async function fetchPolicyOutcomeStats({ policyId, dateRange, versions }) {
    const runOutcomes = await fetchRunOutcomes(
        policyId,
        dateRange.from,
        dateRange.to,
        versions,
    ).catch((error) => {
        console.error(error);
    });

    return { runOutcomes };
}
