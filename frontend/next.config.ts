import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Keep Turbopack scoped to this app when the repository also has a root lockfile.
  // This removes the workspace-root warning and avoids unnecessary file watching.
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
