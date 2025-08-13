"use client";

import { SharedProviders } from "@vulkanlabs/base";

export function Providers({ children }: { children: React.ReactNode }) {
    return <SharedProviders>{children}</SharedProviders>;
}