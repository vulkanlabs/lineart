"use server";

import { fetchRunsCount, fetchRunDurationStats, fetchRunDurationByStatus } from "@/lib/api";

export async function fetchMetricsData({ policyId, dateRange }) {
    const runsCount = await fetchRunsCount(policyId, dateRange.from, dateRange.to).catch(
        (error) => {
            console.error(error);
        },
    );

    const runsByStatus = await fetchRunsCount(policyId, dateRange.from, dateRange.to, true).catch(
        (error) => {
            console.error(error);
        },
    );

    const runDurationStats = await fetchRunDurationStats(
        policyId,
        dateRange.from,
        dateRange.to,
    ).catch((error) => {
        console.error(error);
    });

    const runDurationByStatus = await fetchRunDurationByStatus(
        policyId,
        dateRange.from,
        dateRange.to,
    ).catch((error) => {
        console.error(error);
    });

    return { runsCount, runsByStatus, runDurationStats, runDurationByStatus };
}
