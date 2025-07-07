const baseConfig = require('@vulkan/base/tailwind.config.js');

/** @type {import('tailwindcss').Config} */
module.exports = {
    ...baseConfig,
    content: [
        "./src/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
        "../../packages/base/src/**/*.{js,ts,jsx,tsx,mdx}",
    ],
};