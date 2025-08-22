"use server";

import { createPolicyVersion, deletePolicyVersion } from "@/lib/api";
import { PolicyVersionCreate } from "@vulkanlabs/client-open";
import { handleActionError } from "@/lib/error-handler";

export async function createPolicyVersionAction(data: PolicyVersionCreate) {
    try {
        const response = await createPolicyVersion(data);
        return response;
    } catch (error) {
        handleActionError("create", "policy version", error);
    }
}

export async function deletePolicyVersionAction(policyVersionId: string): Promise<void> {
    try {
        await deletePolicyVersion(policyVersionId);
    } catch (error) {
        handleActionError("delete", "policy version", error);
    }
}
