"use client";

import { VulkanLogo as SharedVulkanLogo, type VulkanLogoConfig } from "@vulkanlabs/base";
import { useRouter, useSearchParams } from "next/navigation";

// Global scope VulkanLogo wrapper
export function VulkanLogo() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const currentProject = searchParams.get("project");

    const handleNavigate = (path: string) => {
        router.push(path);
    };

    const globalScopeLogoConfig: VulkanLogoConfig = {
        homePath: "/",
        useProjectRouting: false,
        currentProject: currentProject || undefined,
        onNavigate: handleNavigate,
    };

    return <SharedVulkanLogo config={globalScopeLogoConfig} />;
}
