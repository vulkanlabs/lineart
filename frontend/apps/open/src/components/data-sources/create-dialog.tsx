"use client";

import { SharedCreateDataSourceDialog } from "@vulkanlabs/base";
import { createDataSourceAction } from "../../app/(app)/integrations/dataSources/actions";

export function CreateDataSourceDialog() {
    return (
        <SharedCreateDataSourceDialog
            config={{
                createDataSource: createDataSourceAction,
            }}
        />
    );
}
