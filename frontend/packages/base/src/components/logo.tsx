interface VulkanLogoProps {
    logoSrc?: string;
    className?: string;
    onClick?: () => void;
}

export function VulkanLogo({
    logoSrc,
    className = "flex items-center gap-2 text-xl font-bold",
    onClick,
}: VulkanLogoProps) {
    return (
        <div
            className={className}
            onClick={onClick}
            style={{ cursor: onClick ? "pointer" : "default" }}
        >
            {logoSrc ? (
                <img src={logoSrc} alt="Vulkan logo" className="max-h-14 max-w-48" />
            ) : (
                <span>Vulkan Engine</span>
            )}
        </div>
    );
}
