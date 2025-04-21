import Link from "next/link";
import Image from "next/image";
import VulkanEngineLogo from "@public/vulkan-engine.png";

export function VulkanLogo() {
    return (
        <Link href="/" className="flex items-center gap-2 text-xl font-bold">
            <Image src={VulkanEngineLogo} alt="Vulkan logo" className="max-h-14 max-w-48" />
        </Link>
    );
}
