"use client";

import { ThemeProvider } from "next-themes";
import { Toaster } from "./toaster";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <ThemeProvider attribute="class" defaultTheme="light">
            {children}
            <Toaster />
        </ThemeProvider>
    );
}
