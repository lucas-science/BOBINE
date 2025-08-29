/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true
  },
  // Désactive la génération de sitemap et autres fichiers non nécessaires
  generateEtags: false,
  distDir: 'out'
}

module.exports = nextConfig