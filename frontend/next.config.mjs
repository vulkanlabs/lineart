/** @type {import('next').NextConfig} */
const nextConfig = {
    experimental: {
        staleTimes: {
            dynamic: 3600,
            static: 3600,
        },
    },
    output: "standalone",
};

export default nextConfig;
