import { NextRequest, NextResponse } from "next/server";
import { fetchRunOutcomes } from "@/lib/api";

export async function POST(request: NextRequest) {
    try {
        const { policyId, dateRange, versions } = await request.json();

        const runOutcomes = await fetchRunOutcomes(
            policyId,
            dateRange.from,
            dateRange.to,
            versions,
        ).catch(() => null);

        return NextResponse.json({ runOutcomes });
    } catch (error) {
        console.error("Failed to get run outcomes:", error);
        return NextResponse.json({ runOutcomes: null }, { status: 500 });
    }
}