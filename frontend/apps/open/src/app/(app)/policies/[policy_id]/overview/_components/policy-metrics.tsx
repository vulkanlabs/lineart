"use client";

import { PolicyMetrics } from "@vulkanlabs/base";
import { PolicyVersion } from "@vulkanlabs/client-open";
import { DateRange } from "react-day-picker";

export default function PolicyMetricsWrapper({
    policyId,
    metricsLoader,
    outcomesLoader,
    versions,
}: {
    policyId: string;
    metricsLoader: (params: {
        policyId: string;
        dateRange: DateRange;
        versions: string[];
    }) => Promise<{
        runsCount?: any[];
        errorRate?: any[];
        runDurationStats?: any[];
        runDurationByStatus?: any[];
    }>;
    outcomesLoader: (params: {
        policyId: string;
        dateRange: DateRange;
        versions: string[];
    }) => Promise<{ runOutcomes: any[] }>;
    versions: PolicyVersion[];
}) {
    return (
        <PolicyMetrics
            config={{
                policyId,
                metricsLoader,
                outcomesLoader,
                versions,
            }}
        />
    );
}
