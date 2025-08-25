"use client";

import { SharedCreatePolicyDialog } from "@vulkanlabs/base";
import { createPolicyClient } from "@/lib/api-client";

export function CreatePolicyDialog() {
    return (
        <SharedCreatePolicyDialog
            config={{
                createPolicy: createPolicyClient,
            }}
        />
    );
}
