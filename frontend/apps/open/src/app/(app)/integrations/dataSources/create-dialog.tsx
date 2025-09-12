"use client";

import { CreateDataSourceDialog as SharedCreateDataSourceDialog } from "@vulkanlabs/base";
import { createDataSource } from "@/lib/api";

export function CreateDataSourceDialog() {
    return (
        <SharedCreateDataSourceDialog
            config={{
                createDataSource,
            }}
        />
    );
}
