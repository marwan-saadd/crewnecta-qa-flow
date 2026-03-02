export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  srcDir: 'src',
  ssr: false,
  modules: ['@nuxt/ui', '@pinia/nuxt'],
  css: ['~/assets/css/main.css'],
  components: [
    { path: '~/components', pathPrefix: false },
  ],
  devServer: { port: 3000 },
  typescript: { strict: true },
  vite: {
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/ws': {
          target: 'ws://localhost:8000',
          ws: true,
        },
      },
    },
  },
  runtimeConfig: {
    public: {
      apiBase: '/api',
      wsBase: '',
    },
  },
})
