"use client";
import Loader from "@/components/animations/loader";
import PolicyMetrics from "./policy-metrics";
import { PolicyVersionsTable } from "./policy-versions-table";
import { fetchMetricsData, fetchPolicyOutcomeStats } from "@/lib/actions";
import { Suspense } from "react";
import { CreatePolicyVersionDialog } from "./create-version";
import { RefreshButton } from "@/components/refresh-button";

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
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div className="flex justify-between">
                <h1 className="text-lg font-semibold md:text-2xl">Versions</h1>
                <div className="flex gap-4">
                    <RefreshButton />
                    <CreatePolicyVersionDialog policyId={policyId} />
                </div>
            </div>
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
