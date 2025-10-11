"use client";

import { type Component } from "@vulkanlabs/client-open";
import {
    ComponentsTable as SharedComponentsTable,
    CreateComponentDialog,
} from "@vulkanlabs/base/components/components";

import { createComponent, deleteComponent } from "@/lib/api";

export function ComponentsTable({ components }: { components: Component[] }) {
    const creationDialog = <CreateComponentDialog config={{ createComponent }} />;

    return (
        <SharedComponentsTable
            components={components}
            config={{
                deleteComponent: deleteComponent,
                CreateComponentDialog: creationDialog,
                resourcePathTemplate: "/components/{resourceId}",
            }}
        />
    );
}
