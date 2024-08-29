import Link from 'next/link';
import Image from 'next/image';
import LogoLight from "/public/vulkan-light.png";

export function VulkanLogo() {
    return (
        <Link href="/" className="flex items-center gap-2 text-xl font-bold">
            <Image src={LogoLight} alt="Vulkan logo" className="max-h-10 max-w-10" />
            <span>Vulkan Engine</span>
        </Link>
    )
}