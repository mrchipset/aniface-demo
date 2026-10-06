import { defineConfig } from 'vite'
import basicSsl from '@vitejs/plugin-basic-ssl'
import fs from 'node:fs'

// 默认使用 HTTPS（浏览器只在 https:// 或 http://localhost 下提供摄像头 API）
// 想强制 HTTP：设置环境变量 HTTPS=0
const haveCert = fs.existsSync('certs/cert.pem') && fs.existsSync('certs/key.pem')
const useHttps = process.env.HTTPS !== '0' && (haveCert || process.env.HTTPS === '1')

export default defineConfig({
  plugins: (useHttps && !haveCert) ? [basicSsl()] : [],
  server: {
    host: true,
    port: 5199,
    strictPort: true,
    ...(useHttps && haveCert
      ? { https: { cert: fs.readFileSync('certs/cert.pem'), key: fs.readFileSync('certs/key.pem') } }
      : {}),
  },
  build: { chunkSizeWarningLimit: 2000 }
})
