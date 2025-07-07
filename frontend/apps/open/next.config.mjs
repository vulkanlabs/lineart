/** @type {import('next').NextConfig} */
const nextConfig = {
    transpilePackages: ['@vulkan/base'],
    experimental: {
        optimizePackageImports: ['@vulkan/base']
    }
};

export default nextConfig;