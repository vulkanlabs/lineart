"use client";

import { SharedCreatePolicyDialog } from "@vulkanlabs/base";
import { createPolicyAction } from "./actions";

export function CreatePolicyDialog() {
    return (
        <SharedCreatePolicyDialog
            config={{
                createPolicy: createPolicyAction,
            }}
        />
    );
}
