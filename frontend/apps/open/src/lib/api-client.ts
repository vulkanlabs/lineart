"use client";

import type { DateRange, MetricsData } from "./api/types";

// Client-side API functions that don't cause server component re-renders

/**
 * Fetch comprehensive metrics for a policy
 * @param {Object} params - Metrics configuration
 * @param {string} params.policyId - Which policy you want metrics for
 * @param {DateRange} params.dateRange - Time period with from/to dates
 * @param {string[]} params.versions - Specific versions to include (empty = all versions)
 * @returns {Promise<MetricsData>} Object containing run counts, error rates, duration stats
 */
export async function fetchMetricsDataClient({
    policyId,
    dateRange,
    versions,
    projectId,
}: {
    policyId: string;
    dateRange: DateRange;
    versions: string[];
    projectId?: string;
}): Promise<MetricsData> {
    try {
        const response = await fetch("/api/metrics", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ policyId, dateRange, versions }),
        });

        if (!response.ok) {
            throw new Error("API request failed");
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch metrics data:", error);
        return {
            runsCount: [],
            errorRate: [],
            runDurationStats: [],
            runDurationByStatus: [],
        };
    }
}

export async function getRunOutcomesByPolicyClient({
    policyId,
    dateRange,
    versions,
    projectId,
}: {
    policyId: string;
    dateRange: any;
    versions: any;
    projectId?: string;
}): Promise<any[]> {
    try {
        const response = await fetch("/api/run-outcomes", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ policyId, dateRange, versions }),
        });

        if (!response.ok) {
            throw new Error("API request failed");
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get run outcomes:", error);
        return [];
    }
}
