import { NextRequest, NextResponse } from "next/server";
import {
    fetchRunsCount,
    fetchRunDurationStats,
    fetchRunDurationByStatus,
} from "@/lib/api";

export async function POST(request: NextRequest) {
    try {
        const { policyId, dateRange, versions } = await request.json();

        const [runsCount, runDurationStats, runDurationByStatus] = await Promise.all([
            fetchRunsCount(policyId, dateRange.from, dateRange.to, versions).catch(() => null),
            fetchRunDurationStats(policyId, dateRange.from, dateRange.to, versions).catch(() => null),
            fetchRunDurationByStatus(policyId, dateRange.from, dateRange.to, versions).catch(() => null),
        ]);

        return NextResponse.json({
            runsCount,
            errorRate: runsCount,
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