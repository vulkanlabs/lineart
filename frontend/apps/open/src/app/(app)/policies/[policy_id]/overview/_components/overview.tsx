"use client";

// React and Next.js
import { Suspense } from "react";

// Vulkan packages
import { Loader } from "@vulkanlabs/base";

// Local imports
import { fetchMetricsDataClient, fetchRunOutcomesClient } from "@/lib/api-client";
import PolicyMetrics from "./policy-metrics";
import { PolicyVersionsTable } from "./policy-versions-table";

type PolicyOverviewPageProps = {
    policyId: string;
    policyData: any;
    policyVersionsData: any;
};

export function PolicyOverviewPage({
    policyId,
    policyData,
    policyVersionsData,
}: PolicyOverviewPageProps) {
    return (
        <div className="flex flex-col gap-4 p-4 lg:p-6">
            <h1 className="text-lg font-semibold md:text-2xl">Versions</h1>
            <Suspense fallback={<Loader />}>
                <PolicyVersionsTable policy={policyData} policyVersions={policyVersionsData} />
            </Suspense>
            <Suspense fallback={<Loader />}>
                <PolicyMetrics
                    policyId={policyId}
                    metricsLoader={fetchMetricsDataClient}
                    outcomesLoader={fetchRunOutcomesClient}
                    versions={policyVersionsData}
                />
            </Suspense>
        </div>
    );
}
