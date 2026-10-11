// 把 MediaPipe 运行时与模型复制/下载到 public/mediapipe/
// 这样启动不再依赖 CDN（大幅降低“有概率卡住/失败”）
// 用法: npm run vendor:mediapipe
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const srcWasm = path.join(root, 'node_modules', '@mediapipe', 'tasks-vision', 'wasm')
const dstDir  = path.join(root, 'public', 'mediapipe')
const dstWasm = path.join(dstDir, 'wasm')
const MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
const modelPath = path.join(dstDir, 'face_landmarker.task')

if (!fs.existsSync(srcWasm)) {
  console.error('❌ 找不到 node_modules/@mediapipe/tasks-vision/wasm，请先 npm install')
  process.exit(1)
}

fs.mkdirSync(dstWasm, { recursive: true })
let copied = 0, bytes = 0
for (const f of fs.readdirSync(srcWasm)) {
  const s = path.join(srcWasm, f), d = path.join(dstWasm, f)
  fs.copyFileSync(s, d)
  copied++; bytes += fs.statSync(d).size
}
console.log(`✅ WASM: 复制 ${copied} 个文件 (${(bytes / 1048576).toFixed(1)} MB) -> public/mediapipe/wasm`)

if (fs.existsSync(modelPath)) {
  console.log(`✅ 模型: 已存在 (${(fs.statSync(modelPath).size / 1048576).toFixed(2)} MB)`)
} else {
  console.log('⏬ 下载 face_landmarker.task …')
  const res = await fetch(MODEL_URL)
  if (!res.ok) { console.error('❌ 模型下载失败 HTTP ' + res.status); process.exit(1) }
  fs.writeFileSync(modelPath, Buffer.from(await res.arrayBuffer()))
  console.log(`✅ 模型: ${(fs.statSync(modelPath).size / 1048576).toFixed(2)} MB -> public/mediapipe/face_landmarker.task`)
}
