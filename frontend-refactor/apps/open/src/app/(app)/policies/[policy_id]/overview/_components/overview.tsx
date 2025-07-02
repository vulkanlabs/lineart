"use client";
import { Suspense } from "react";
import { Loader } from "@vulkan/base";
import { fetchMetricsData, fetchPolicyOutcomeStats } from "@/lib/actions";

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
                    metricsLoader={fetchMetricsData}
                    outcomesLoader={fetchPolicyOutcomeStats}
                    versions={policyVersionsData}
                />
            </Suspense>
        </div>
    );
}
