import { NextRequest, NextResponse } from "next/server";
import { fetchPolicyRuns, fetchPolicyVersionRuns } from "@/lib/api";

export async function POST(request: NextRequest) {
    try {
        const { type, resourceId, dateRange } = await request.json();

        let runs = null;
        
        if (type === "policy") {
            runs = await fetchPolicyRuns(resourceId, dateRange.from, dateRange.to).catch(() => null);
        } else if (type === "policyVersion") {
            runs = await fetchPolicyVersionRuns(resourceId, dateRange.from, dateRange.to).catch(() => null);
        }

        return NextResponse.json({ runs });
    } catch (error) {
        console.error("Failed to fetch runs:", error);
        return NextResponse.json({ runs: null }, { status: 500 });
    }
}