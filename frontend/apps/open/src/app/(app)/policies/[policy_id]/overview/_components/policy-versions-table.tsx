"use client";

import { PolicyVersionsTable as SharedPolicyVersionsTable } from "@vulkanlabs/base";
import type { Policy, PolicyVersion } from "@vulkanlabs/client-open";

import { deletePolicyVersion } from "@/lib/api";
import { CreatePolicyVersionDialog } from "./create-version";

export function PolicyVersionsTable({
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
