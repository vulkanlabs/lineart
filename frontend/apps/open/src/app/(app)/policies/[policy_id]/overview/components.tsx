"use client";

// React and Next.js
import { Suspense } from "react";

// Vulkan packages
import type { Policy, PolicyVersion } from "@vulkanlabs/client-open";
import {
    PolicyVersionsTable as SharedPolicyVersionsTable,
    CreatePolicyVersionDialog as SharedCreatePolicyVersionDialog,
    Loader,
    PolicyMetrics,
} from "@vulkanlabs/base";

// Local imports
import {
    createPolicyVersion,
    deletePolicyVersion,
    fetchPolicyMetrics,
    fetchRunOutcomes,
} from "@/lib/api";

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
                    config={{
                        policyId,
                        metricsLoader: fetchPolicyMetrics,
                        outcomesLoader: fetchRunOutcomes,
                        versions: policyVersionsData,
                    }}
                />
            </Suspense>
        </div>
    );
}

function PolicyVersionsTable({
    policy,
    policyVersions,
}: {
    policy: Policy;
    policyVersions: PolicyVersion[];
}) {
    return (
        <SharedPolicyVersionsTable
            config={{
                policy,
                policyVersions,
                deletePolicyVersion,
                CreateVersionDialog: CreatePolicyVersionDialog,
            }}
        />
    );
}

function CreatePolicyVersionDialog({ policyId }: { policyId: string }) {
    return (
        <SharedCreatePolicyVersionDialog
            config={{
                policyId,
                createPolicyVersion,
            }}
        />
    );
}
