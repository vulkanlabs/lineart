"use client";

import { CreateDataSourceDialog, CreateDataSourceDialogConfig } from "@vulkanlabs/base";
import { createDataSourceAction } from "../../app/(app)/integrations/dataSources/actions";

const ossConfig: CreateDataSourceDialogConfig = {
    createAction: createDataSourceAction,
};

export function OSSCreateDataSourceDialog() {
    return <CreateDataSourceDialog config={ossConfig} />;
}