"use client";

import * as React from "react";
import VulkanEngineLogo from "../assets/vulkan-engine.png";

export interface VulkanLogoConfig {
    /** Function to transform the home path with project context */
    withProject?: (path: string, project?: string) => string;
    /** Custom home path (defaults to "/") */
    homePath?: string;
    /** Whether to use project-aware routing */
    useProjectRouting?: boolean;
    /** Current project ID for routing context */
    currentProject?: string;
    /** Navigation callback for framework-agnostic routing */
    onNavigate?: (path: string) => void;
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
    const { 
        withProject, 
        homePath = "/", 
        useProjectRouting = false, 
        currentProject, 
        onNavigate 
    } = config;

    const handleClick = () => {
        if (onClick) {
            onClick();
        } else if (onNavigate) {
            // For navigation behavior
            let href = homePath;
            if (useProjectRouting && withProject) {
                href = withProject(homePath, currentProject || undefined);
            }
            onNavigate(href);
        }
    };

    return (
        <div 
            className={className} 
            onClick={handleClick} 
            style={{ cursor: "pointer" }}
        >
            <img 
                src={VulkanEngineLogo} 
                alt="Vulkan logo" 
                className="max-h-14 max-w-48" 
            />
        </div>
    );
}
