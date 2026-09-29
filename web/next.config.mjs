/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    const gatewayUrl = process.env.GATEWAY_URL || process.env.GATEWAY_INTERNAL_URL || "http://gateway:5000";
    return [
      {
        source: "/api/:path*",
        destination: `${gatewayUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
