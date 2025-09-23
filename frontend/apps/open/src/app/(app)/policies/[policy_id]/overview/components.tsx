"use client";

// React and Next.js
import { Suspense } from "react";

// Vulkan packages
import type { Policy, PolicyVersion } from "@vulkanlabs/client-open";
import {
    PolicyVersionsTable as SharedPolicyVersionsTable,
    CreatePolicyVersionDialog as SharedCreatePolicyVersionDialog,
    PolicyMetrics,
} from "@vulkanlabs/base/components/policies";
import { Loader } from "@vulkanlabs/base";

// Local imports
import {
    createPolicyVersion,
    deletePolicyVersion,
    fetchPolicyMetrics,
    fetchRunOutcomesForMetrics,
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
                        outcomesLoader: fetchRunOutcomesForMetrics,
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
    const handleCreatePolicyVersion = async (data: { policy_id: string; alias?: string }) => {
        // Convert to PolicyVersionBase format
        const policyVersionData = {
            policy_id: data.policy_id,
            alias: data.alias || null, // Convert undefined to null
        };
        return createPolicyVersion(policyVersionData);
    };

    return (
        <SharedCreatePolicyVersionDialog
            config={{
                policyId,
                createPolicyVersion: handleCreatePolicyVersion,
            }}
        />
    );
}
