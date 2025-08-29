"use client";

import { SharedCreatePolicyDialog } from "@vulkanlabs/base";
import { createPolicy } from "@/lib/api";

export function CreatePolicyDialog() {
    return (
        <SharedCreatePolicyDialog
            config={{
                createPolicy: createPolicy,
            }}
        />
    );
}
