const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    module: {
      rules: [
        {
          test: /\.md$/,
          use: 'raw-loader'
        }
      ]
    }
  },
  devServer: {
    allowedHosts: 'all',
    host: '0.0.0.0',
    port: 3000,
    client: {
      webSocketURL: 'wss://dev2.icarostangent.lab/ws'
    },
    proxy: {
      '/': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:3000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
