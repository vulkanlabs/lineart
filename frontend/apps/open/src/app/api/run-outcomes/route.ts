import { NextRequest, NextResponse } from "next/server";
import { fetchRunOutcomes } from "@/lib/api";

export async function POST(request: NextRequest) {
    try {
        const { policyId, dateRange, versions } = await request.json();

        const runOutcomes = await fetchRunOutcomes(
            policyId,
            new Date(dateRange.from),
            new Date(dateRange.to),
            versions,
        );

        return NextResponse.json(runOutcomes);
    } catch (error) {
        console.error("Failed to get run outcomes:", error);
        return NextResponse.json({ error: `Internal Server Error: ${error}` }, { status: 500 });
    }
}
