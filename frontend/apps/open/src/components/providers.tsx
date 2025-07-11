"use client";

import { Toaster } from "@vulkanlabs/base/ui";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <>
            {children}
            <Toaster />
        </>
    );
}
