import { ComponentsTable as SharedComponentsTable } from "@vulkanlabs/base";
import { type Component } from "@vulkanlabs/client-open";
import { deleteComponentAction } from "./actions";
import { CreateComponentDialog } from "./create-dialog";

export function ComponentsTable({ components }: { components: Component[] }) {
    return (
        <SharedComponentsTable
            components={components}
            config={{
                mode: "full",
                deleteComponent: deleteComponentAction,
                CreateComponentDialog: <CreateComponentDialog />,
            }}
        />
    );
}
