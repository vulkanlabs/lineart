"use server";

import { createPolicy } from "@/lib/api";
import { Policy } from "@vulkan/client-open/models/Policy";
import { PolicyBase } from "@vulkan/client-open/models/PolicyBase";

export async function createPolicyAction(data: PolicyBase): Promise<Policy> {
    try {
        const response = await createPolicy(data);
        return response;
    } catch (error) {
        console.error("Error creating policy:", error);
        throw new Error("Failed to create policy");
    }
}
