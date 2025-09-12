"use client";

import { CreatePolicyVersionDialog as SharedCreatePolicyVersionDialog } from "@vulkanlabs/base";
import { createPolicyVersion } from "@/lib/api";

export function CreatePolicyVersionDialog({ policyId }: { policyId: string }) {
    return (
        <SharedCreatePolicyVersionDialog
            config={{
                policyId,
                createPolicyVersion,
            }}
        />
    );
}
