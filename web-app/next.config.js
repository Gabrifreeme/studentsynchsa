/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable server-side features for Drizzle
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
};

module.exports = nextConfig;
