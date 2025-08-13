"use client";

import Link from "next/link";
import Image from "next/image";
import { useSearchParams } from "next/navigation";

export interface VulkanLogoConfig {
    /** Function to transform the home path with project context */
    withProject?: (path: string, project?: string) => string;
    /** Logo image source (apps should provide their logo import) */
    logoSrc?: any;
    /** Custom home path (defaults to "/") */
    homePath?: string;
    /** Whether to use project-aware routing */
    useProjectRouting?: boolean;
}

export interface VulkanLogoProps {
    config?: VulkanLogoConfig;
    className?: string;
    onClick?: () => void;
}

export function VulkanLogo({
    config = {},
    className = "flex items-center gap-2 text-xl font-bold",
    onClick,
}: VulkanLogoProps) {
    const { withProject, logoSrc, homePath = "/", useProjectRouting = false } = config;
    const searchParams = useSearchParams();
    const currentProject = searchParams.get("project");
    
    // For click-only behavior (no navigation)
    if (onClick) {
        return (
            <div
                className={className}
                onClick={onClick}
                style={{ cursor: "pointer" }}
            >
                {logoSrc ? (
                    <Image src={logoSrc} alt="Vulkan logo" className="max-h-14 max-w-48" />
                ) : (
                    <span>Vulkan Engine</span>
                )}
            </div>
        );
    }

    // For navigation behavior
    let href = homePath;
    if (useProjectRouting && withProject) {
        href = withProject(homePath, currentProject || undefined);
    }
    
    return (
        <Link href={href} className={className}>
            {logoSrc ? (
                <Image src={logoSrc} alt="Vulkan logo" className="max-h-14 max-w-48" />
            ) : (
                <span>Vulkan Engine</span>
            )}
        </Link>
    );
}
