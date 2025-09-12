"use client";

import { CreateComponentDialog as SharedCreateComponentDialog } from "@vulkanlabs/base";
import { createComponent } from "@/lib/api";

export function CreateComponentDialog() {
    return (
        <SharedCreateComponentDialog
            config={{
                createComponent,
            }}
        />
    );
}
