"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * SSimple Navigation Guard
 *
 * Covers the two most important internal navigation scenarios:
 * - Link components
 * - Programmatic router.push/replace calls
 */
export function NavigationGuard() {
    const router = useRouter();

    useEffect(() => {
        // Check if AutoSaveToggle has unsaved changes
        const hasUnsavedChanges = () => {
            const checkFn = (window as any).checkUnsavedChanges;
            return checkFn ? !checkFn(() => {}) : false;
        };

        // Store original router methods
        const originalPush = router.push;
        const originalReplace = router.replace;

        // Wrap router methods with unsaved changes check
        router.push = (href: string, options?: any) => {
            if (hasUnsavedChanges()) {
                const confirmed = window.confirm(
                    "You have unsaved changes that will be lost. Continue anyway?"
                );
                if (!confirmed) return;
            }
            originalPush(href, options);
        };

        router.replace = (href: string, options?: any) => {
            if (hasUnsavedChanges()) {
                const confirmed = window.confirm(
                    "You have unsaved changes that will be lost. Continue anyway?"
                );
                if (!confirmed) return;
            }
            originalReplace(href, options);
        };

        // Intercept Link component clicks
        const handleLinkClick = (event: MouseEvent) => {
            const target = event.target as HTMLElement;
            const link = target.closest("a");

            if (link?.href && !link.target && link.href.startsWith(window.location.origin)) {
                if (hasUnsavedChanges()) {
                    const confirmed = window.confirm(
                        "You have unsaved changes that will be lost. Continue anyway?"
                    );
                    if (!confirmed) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                }
            }
        };

        document.addEventListener("click", handleLinkClick, true);

        return () => {
            router.push = originalPush;
            router.replace = originalReplace;
            document.removeEventListener("click", handleLinkClick, true);
        };
    }, [router]);

    return null;
}