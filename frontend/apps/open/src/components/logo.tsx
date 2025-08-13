import { VulkanLogo as SharedVulkanLogo, type VulkanLogoConfig } from "@vulkanlabs/base";
import VulkanEngineLogo from "@public/vulkan-engine.png";

// Local logo configuration
const logoConfig: VulkanLogoConfig = {
    logoSrc: VulkanEngineLogo,
    homePath: "/",
    useProjectRouting: false,
};

// Local VulkanLogo wrapper
export function VulkanLogo() {
    return <SharedVulkanLogo config={logoConfig} />;
}
