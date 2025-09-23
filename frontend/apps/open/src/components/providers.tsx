"use client";

import { ThemeProvider } from "next-themes";
import { ToastProvider, ToastContainer } from "@vulkanlabs/base";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <ThemeProvider attribute="class" defaultTheme="light">
            <ToastProvider>
                {children}
                <ToastContainer />
            </ToastProvider>
        </ThemeProvider>
    );
}
