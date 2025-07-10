"use server";

import { Run } from "@vulkan/client-open";
import {
    fetchPolicyRuns,
    fetchPolicyVersionRuns,
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

export async function fetchRunsByPolicy({
    resourceId,
    dateRange,
}): Promise<{ runs: Run[] | null }> {
    const runs = await fetchPolicyRuns(resourceId, dateRange.from, dateRange.to).catch((error) => {
        console.error(error);
    });
    if (!runs) {
        return { runs: null };
    }

    return { runs };
}

export async function fetchRunsByPolicyVersion({
    resourceId,
    dateRange,
}): Promise<{ runs: Run[] | null }> {
    const runs = await fetchPolicyVersionRuns(resourceId, dateRange.from, dateRange.to).catch(
        (error) => {
            console.error(error);
        },
    );
    if (!runs) {
        return { runs: null };
    }

    return { runs };
}
