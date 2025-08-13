"use client";

import { ThemeProvider } from "next-themes";
import { SharedToaster } from "./shared-toaster";

export function SharedProviders({ children }: { children: React.ReactNode }) {
    return (
        <ThemeProvider attribute="class" defaultTheme="light">
            {children}
            <SharedToaster />
        </ThemeProvider>
    );
}