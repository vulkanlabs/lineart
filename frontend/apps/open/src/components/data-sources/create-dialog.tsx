"use client";

import { Suspense } from "react";
import { SharedCreateDataSourceDialog } from "@vulkanlabs/base";
import { createDataSourceAction } from "../../app/(app)/integrations/dataSources/actions";

export function CreateDataSourceDialog() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <SharedCreateDataSourceDialog
                config={{
                    createDataSource: createDataSourceAction,
                }}
            />
        </Suspense>
    );
}
