"use client";

import { useRouter } from "next/navigation";

import { type Component } from "@vulkanlabs/client-open";
import { ComponentsTable as SharedComponentsTable, CreateComponentDialog } from "@vulkanlabs/base";

import { createComponent, deleteComponent } from "@/lib/api";

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
                deleteComponent: deleteComponent,
                CreateComponentDialog: (
                    <CreateComponentDialog
                        config={{
                            createComponent,
                        }}
                    />
                ),
                onRefresh: handleRefresh,
                onNavigate: handleNavigate,
            }}
        />
    );
}
