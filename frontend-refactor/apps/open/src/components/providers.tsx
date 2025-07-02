"use client";

import { Toaster } from "@vulkan/base/ui";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <>
            {children}
            <Toaster />
        </>
    );
}