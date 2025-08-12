// Local imports
import { ComponentsTable as SharedComponentsTable } from "@vulkanlabs/base";
import { type Component } from "@vulkanlabs/client-open";
import { deleteComponent } from "@/lib/api";
import { CreateComponentDialog } from "@/app/(app)/components/create-dialog";

export function ComponentsTable({ components }: { components: Component[] }) {
    return (
        <SharedComponentsTable
            components={components}
            config={{
                mode: "full",
                deleteComponent: (id) => deleteComponent(id),
                CreateComponentDialog: <CreateComponentDialog />,
            }}
        />
    );
}
