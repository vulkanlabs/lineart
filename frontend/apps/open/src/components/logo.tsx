import { VulkanLogo as SharedVulkanLogo, type VulkanLogoConfig } from "@vulkanlabs/base";
import VulkanEngineLogo from "@public/vulkan-engine.png";

// Global scope logo configuration
const globalScopeLogoConfig: VulkanLogoConfig = {
    logoSrc: VulkanEngineLogo,
    homePath: "/",
    useProjectRouting: false,
};

// Global scope VulkanLogo wrapper
export function VulkanLogo() {
    return <SharedVulkanLogo config={globalScopeLogoConfig} />;
}
