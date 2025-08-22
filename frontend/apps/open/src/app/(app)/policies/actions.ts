"use server";

import { createPolicy, deletePolicy } from "@/lib/api";
import { Policy, PolicyCreate } from "@vulkanlabs/client-open";
import { handleActionError } from "@/lib/error-handler";

export async function createPolicyAction(data: PolicyCreate): Promise<Policy> {
    try {
        const response = await createPolicy(data);
        return response;
    } catch (error) {
        handleActionError("create", "policy", error);
    }
}

export async function deletePolicyAction(policyId: string): Promise<void> {
    try {
        await deletePolicy(policyId);
    } catch (error) {
        handleActionError("delete", "policy", error);
    }
}
