import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Minimal, self-contained build output for the Dockerfile (Stage 15 containers) —
  // see https://nextjs.org/docs/app/getting-started/deploying#docker.
  output: "standalone",
};

export default nextConfig;
