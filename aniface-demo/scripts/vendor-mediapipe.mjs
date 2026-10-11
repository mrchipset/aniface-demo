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
const SEG_URL   = 'https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/1/selfie_segmenter.tflite'
const segPath   = path.join(dstDir, 'selfie_segmenter.tflite')

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
  await download(MODEL_URL, modelPath, 'face_landmarker.task')
}

if (fs.existsSync(segPath)) {
  console.log(`✅ 分割模型: 已存在 (${(fs.statSync(segPath).size / 1024).toFixed(1)} KB)`)
} else {
  console.log('⏬ 下载 selfie_segmenter.tflite …（背景虚化用）')
  await download(SEG_URL, segPath, 'selfie_segmenter.tflite')
}

async function download(url, dst, label) {
  const res = await fetch(url)
  if (!res.ok) { console.error(`❌ ${label} 下载失败 HTTP ${res.status}`); process.exit(1) }
  fs.writeFileSync(dst, Buffer.from(await res.arrayBuffer()))
  const kb = fs.statSync(dst).size / 1024
  console.log(`✅ ${label}: ${kb > 1024 ? (kb / 1024).toFixed(2) + ' MB' : kb.toFixed(1) + ' KB'} -> ${path.relative(root, dst)}`)
}
