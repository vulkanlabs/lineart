"use client";

import { ComponentsTable as SharedComponentsTable } from "@vulkanlabs/base";
import { type Component } from "@vulkanlabs/client-open";
import { useRouter } from "next/navigation";
import { deleteComponentAction } from "./actions";
import { CreateComponentDialog } from "./create-dialog";

export function ComponentsTable({ components }: { components: Component[] }) {
    const router = useRouter();

    const handleRefresh = () => {
        router.refresh();
    };

    const handleNavigate = (path: string) => {
        router.push(path);
    };

    return (
        <SharedComponentsTable
            components={components}
            config={{
                mode: "full",
                deleteComponent: deleteComponentAction,
                CreateComponentDialog: <CreateComponentDialog />,
                onRefresh: handleRefresh,
                onNavigate: handleNavigate,
            }}
        />
    );
}
