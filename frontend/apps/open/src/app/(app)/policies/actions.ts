"use server";

import { createPolicy } from "@/lib/api";
import { Policy, PolicyBase } from "@vulkan/client-open";

export async function createPolicyAction(data: PolicyBase): Promise<Policy> {
    try {
        const response = await createPolicy(data);
        return response;
    } catch (error) {
        console.error("Error creating policy:", error);
        throw new Error("Failed to create policy");
    }
}
