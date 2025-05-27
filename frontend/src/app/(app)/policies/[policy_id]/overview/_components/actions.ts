"use server";

import { createPolicyVersion } from "@/lib/api";
import { PolicyVersionCreate } from "@vulkan-server/PolicyVersionCreate";

export async function createPolicyVersionAction(data: PolicyVersionCreate) {
    try {
        const response = await createPolicyVersion(data);
        return response;
    } catch (error) {
        console.error("Error creating policy version:", error);
        throw new Error("Failed to create policy version");
    }
}
