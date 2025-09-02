import { NextRequest, NextResponse } from "next/server";
import {
    fetchRunsCount,
    fetchRunDurationStats,
    fetchRunDurationByStatus,
    fetchRunOutcomes,
} from "@/lib/api";

/**
 * Metrics aggregation API endpoint - get policy analytics data
 * POST /api/metrics
 *
 * @param {NextRequest} request - HTTP request with JSON body
 * @returns {NextResponse} Aggregated metrics data or error response
 *
 * Request body: { policyId: string, dateRange: {from: Date, to: Date}, versions: string[] }
 * Response: { runsCount, errorRate, runDurationStats, runDurationByStatus }
 *
 * Fetches multiple metrics in parallel, calculates error rates, handles failures
 * Returns null for failed metrics instead of failing entirely
 */
export async function POST(request: NextRequest) {
    try {
        const { policyId, dateRange, versions } = await request.json();

        const [runsCount, runDurationStats, runDurationByStatus] = await Promise.all([
            fetchRunsCount(policyId, dateRange.from, dateRange.to, versions).catch(() => null),
            fetchRunDurationStats(policyId, dateRange.from, dateRange.to, versions).catch(
                () => null,
            ),
            fetchRunDurationByStatus(policyId, dateRange.from, dateRange.to, versions).catch(
                () => null,
            ),
        ]);

        // Calculate error rate from runs data if available
        let errorRate = null;
        if (runsCount && Array.isArray(runsCount)) {
            errorRate = runsCount.map((dayData: any) => ({
                date: dayData.date,
                error_rate: dayData.error_rate || 0,
            }));
        }

        return NextResponse.json({
            runsCount,
            errorRate,
            runDurationStats,
            runDurationByStatus,
        });
    } catch (error) {
        console.error("Failed to fetch metrics data:", error);
        return NextResponse.json(
            {
                runsCount: null,
                errorRate: null,
                runDurationStats: null,
                runDurationByStatus: null,
            },
            { status: 500 },
        );
    }
}
