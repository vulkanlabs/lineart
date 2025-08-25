"use client";

import { ComponentsTable as SharedComponentsTable } from "@vulkanlabs/base";
import { type Component } from "@vulkanlabs/client-open";
import { useRouter } from "next/navigation";
import { deleteComponentClient } from "@/lib/api-client";
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
                deleteComponent: deleteComponentClient,
                CreateComponentDialog: <CreateComponentDialog />,
                onRefresh: handleRefresh,
                onNavigate: handleNavigate,
            }}
        />
    );
}
