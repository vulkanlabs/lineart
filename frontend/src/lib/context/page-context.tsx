/**
 * React context provider for page context
 */

"use client";

import { createContext, useContext, useEffect, ReactNode } from "react";
import { usePathname, useParams } from "next/navigation";
import { contextManager } from "./context-manager";
import { PageContext } from "./types";

interface PageContextProviderProps {
    children: ReactNode;
}

const PageContextContext = createContext<{
    context: PageContext;
    updateContext: (context: Partial<PageContext>) => void;
    updateData: (data: Partial<PageContext["data"]>) => void;
} | null>(null);

export function PageContextProvider({ children }: PageContextProviderProps) {
    const pathname = usePathname();
    const params = useParams();

    // Update context when route changes
    useEffect(() => {
        const routeParams = Array.isArray(params) ? {} : params || {};
        contextManager.updateFromRoute(pathname, routeParams as Record<string, string>);
    }, [pathname, params]);

    const updateContext = (context: Partial<PageContext>) => {
        contextManager.setContext(context);
    };

    const updateData = (data: Partial<PageContext["data"]>) => {
        contextManager.updateContextData(data);
    };

    return (
        <PageContextContext.Provider
            value={{
                context: contextManager.getCurrentContext(),
                updateContext,
                updateData,
            }}
        >
            {children}
        </PageContextContext.Provider>
    );
}

export function usePageContext() {
    const context = useContext(PageContextContext);
    if (!context) {
        throw new Error("usePageContext must be used within a PageContextProvider");
    }
    return context;
}

// Hook specifically for checking if on workflow page
export function useIsWorkflowPage(): boolean {
    const { context } = usePageContext();
    return context.page === "workflow";
}
