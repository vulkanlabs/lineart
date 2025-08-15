"use client";

import { SharedCreateDataSourceDialog, CreateDataSourceDialogConfig } from "@vulkanlabs/base";
import { createDataSourceAction } from "../../app/(app)/integrations/dataSources/actions";

export function CreateDataSourceDialog() {
    return (
        <SharedCreateDataSourceDialog
            config={{
                createDataSource: async (dataSourceSpec) => {
                    return await createDataSourceAction(dataSourceSpec);
                },
            }}
        />
    );
}
