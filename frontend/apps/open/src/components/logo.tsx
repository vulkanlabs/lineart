"use client";

import { useRouter, useSearchParams } from "next/navigation";

// Global scope VulkanLogo wrapper
export function VulkanLogo() {
    const router = useRouter();
    const searchParams = useSearchParams();

    const handleClick = () => {
        router.push("/");
    };

    return (
        <div
            className="flex items-center gap-2 text-xl font-bold"
            onClick={handleClick}
            style={{ cursor: "pointer" }}
        >
            <img src="/assets/vulkan-engine.png" alt="Vulkan logo" className="max-h-14 max-w-48" />
        </div>
    );
}
