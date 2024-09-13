import { Inter } from "next/font/google";
import "@/app/globals.css";
import { StackProvider, StackTheme } from "@stackframe/stack";
import { stackServerApp } from "@/stack";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Vulkan Engine",
  description: "Workspace for policies in Vulkan",
};

export default function RootLayout({ children }) {
    return (
      <html lang="en">
        <body className={inter.className}>
          <StackProvider  app={stackServerApp}>
            <StackTheme>
            {children}
            </StackTheme>
          </StackProvider>
        </body>
      </html>
    )
}
