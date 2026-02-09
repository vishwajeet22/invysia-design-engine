/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/createOrder',
        destination: 'https://plutus-server-268314723675.us-central1.run.app/createOrder',
      },
      {
        source: '/run_sse',
        destination: 'https://daedalus-engine-268314723675.us-central1.run.app/run_sse',
      },
      {
        source: '/apps/:path*',
        destination: 'https://daedalus-engine-268314723675.us-central1.run.app/apps/:path*',
      }
    ]
  },
};

export default nextConfig;
