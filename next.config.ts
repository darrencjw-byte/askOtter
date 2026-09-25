import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // [VIBER] Disable RSC render cache and Enable Turbopack FS cache so edits are reflected immediately.
  experimental: { serverComponentsHmrCache: false, turbopackFileSystemCacheForDev: true },
  // [VIBER] Allow Next dev client/HMR through sandbox preview hosts.
  allowedDevOrigins: [
    '*.cio.sandbox.gov.sg',
    '*.cio-uat.sandbox.gov.sg',
    '**.code.run',
  ],
  output: "standalone",
  // self-heal's build-check runs `npm run build` after every response as
  // a proxy for the POC deploy. Without this, that build writes into the
  // same `.next` the dev server (Turbopack) is live-serving from, which
  // corrupts the running preview and forces a restart almost every time.
  // Routing it to a separate dir removes that collision — and has zero
  // effect on the real POC deploy, which builds in its own clean
  // container without this env var set.
  distDir: process.env.SELF_HEAL_BUILD_CHECK ? ".next-buildcheck" : ".next",
  devIndicators: false,
  reactStrictMode: true,
  images: {
    dangerouslyAllowSVG: true,
    contentDispositionType: "attachment",
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },
  turbopack: {},
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
        ],
      },
    ];
  },
};

export default nextConfig;
