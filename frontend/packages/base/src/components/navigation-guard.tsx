"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Navigation Guard - Prevents navigation with unsaved changes
 */
export function NavigationGuard() {
    const router = useRouter();

    useEffect(() => {
        const hasUnsavedChanges = () => {
            const checkFn = (window as any).checkUnsavedChanges;
            return checkFn ? !checkFn(() => {}) : false;
        };

        const confirmNavigation = () => {
            if (!hasUnsavedChanges()) return true;
            return window.confirm("You have unsaved changes that will be lost. Continue anyway?");
        };

        // Wrap router methods
        const originalPush = router.push;
        const originalReplace = router.replace;

        router.push = (href: string, options?: any) => {
            if (confirmNavigation()) originalPush(href, options);
        };

        router.replace = (href: string, options?: any) => {
            if (confirmNavigation()) originalReplace(href, options);
        };

        // Handle link clicks
        const handleLinkClick = (e: MouseEvent) => {
            const link = (e.target as HTMLElement).closest("a");
            if (!link?.href || link.target || !link.href.startsWith(window.location.origin)) return;

            if (!confirmNavigation()) {
                e.preventDefault();
                e.stopPropagation();
            }
        };

        // Handle browser navigation
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (hasUnsavedChanges()) {
                e.preventDefault();
                e.returnValue = "";
            }
        };

        document.addEventListener("click", handleLinkClick, true);
        window.addEventListener("beforeunload", handleBeforeUnload);

        return () => {
            router.push = originalPush;
            router.replace = originalReplace;
            document.removeEventListener("click", handleLinkClick, true);
            window.removeEventListener("beforeunload", handleBeforeUnload);
        };
    }, [router]);

    return null;
}
