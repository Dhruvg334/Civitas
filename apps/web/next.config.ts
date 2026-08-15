import type { NextConfig } from "next";

const isStandalone =
  !process.env.VERCEL &&
  (process.env.BUILD_STANDALONE === "true" || process.env.DOCKER_BUILD === "true");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  ...(isStandalone ? { output: "standalone" } : {}),
};

export default nextConfig;
