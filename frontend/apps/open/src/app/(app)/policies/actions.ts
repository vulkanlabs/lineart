"use server";

import { createPolicy } from "@/lib/api";
import { Policy, PolicyCreate } from "@vulkanlabs/client-open";

export async function createPolicyAction(data: PolicyCreate): Promise<Policy> {
    try {
        const response = await createPolicy(data);
        return response;
    } catch (error) {
        console.error("Error creating policy:", error);
        throw new Error("Failed to create policy");
    }
}
