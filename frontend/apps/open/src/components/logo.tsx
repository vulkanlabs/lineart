import { VulkanLogo as SharedVulkanLogo, type VulkanLogoConfig } from "@vulkanlabs/base";
import VulkanEngineLogo from "@public/vulkan-engine.png";

// OSS-specific configuration
const ossLogoConfig: VulkanLogoConfig = {
    logoSrc: VulkanEngineLogo,
    homePath: "/",
    useProjectRouting: false,
};

// OSS-specific VulkanLogo wrapper
export function VulkanLogo() {
    return <SharedVulkanLogo config={ossLogoConfig} />;
}
