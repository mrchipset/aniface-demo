import { Aniface } from 'aniface'
import * as THREE from 'three'
import { FaceLandmarker, FilesetResolver } from '@mediapipe/tasks-vision'

const WASM  = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm'
const MODEL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'

const canvas = document.getElementById('avatar')
const video  = document.getElementById('webcam')
const frame  = document.getElementById('frame')
const statusEl = document.getElementById('status')
const setStatus = (t) => { statusEl.textContent = t; console.log('[status]', t) }

let avatar = null, landmarker = null, camStream = null, playing = false, wrapper = null

// ---------------- 环境自检 ----------------
function cameraProblem() {
  if (!window.isSecureContext)
    return '当前不是「安全上下文」。摄像头 API 只在 https:// 或 http://localhost 下可用。\n你现在访问的是：' + location.origin
  if (!navigator.mediaDevices) return 'navigator.mediaDevices 不存在（浏览器过旧，或页面在受限 iframe 里）'
  if (!navigator.mediaDevices.getUserMedia) return '浏览器不支持 getUserMedia'
  return null
}
window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('diag').textContent =
    'origin=' + location.origin + ' · secure=' + window.isSecureContext + ' · mediaDevices=' + !!navigator.mediaDevices
  const p = cameraProblem(); if (p) setStatus('⚠️ ' + p)
})

// ---------------- 模型 ----------------
async function ensureAvatar() {
  if (avatar) return avatar
  setStatus('加载模型…')
  avatar = new Aniface({
    canvasElement: canvas,
    modelPath: '/redpanda_head.glb',
    cameraConfig: { fov: 40, enableControls: true, enableZoom: true },
    blendshapeMultipliers: {
      eyeBlinkLeft: 1.2, eyeBlinkRight: 1.2, jawOpen: 1.0,
      mouthSmileLeft: 1.1, mouthSmileRight: 1.1, browInnerUp: 1.2
    },
    modelOptions: { scale: 1.0, center: true, autoRotate: false, rotation: 0 },
    onReady: () => { setStatus('模型就绪 ✅'); ensureWrapper(); applyTransform() },
    onError: (e) => setStatus('模型错误: ' + e.message)
  })
  await avatar.initialize()
  ensureWrapper()
  return avatar
}

// head-only 分支下 aniface 每帧会覆盖 gltf.scene.matrix，
// 所以把模型塞进我们自己的 Group，位置/缩放改在 Group 上才不会被覆盖
function ensureWrapper() {
  if (wrapper || !avatar) return
  const inner = avatar.getRenderer()?.getAvatar()?.getScene()
  if (!inner || !inner.parent) return
  wrapper = new THREE.Group()
  inner.parent.add(wrapper)
  wrapper.add(inner)
  wrapper.position.set(0, 0, 0)
  wrapper.scale.setScalar(1)
  console.log('wrapper group created')
}

// ---------------- 位置 / 缩放 ----------------
const T = { scale: 't_scale', x: 't_x', y: 't_y', z: 't_z' }
function applyTransform() {
  if (!wrapper) return
  const g = (k) => parseFloat(document.getElementById(T[k]).value)
  const s = g('scale')
  document.getElementById('tv_scale').textContent = s.toFixed(2)
  document.getElementById('tv_x').textContent = g('x').toFixed(2)
  document.getElementById('tv_y').textContent = g('y').toFixed(2)
  document.getElementById('tv_z').textContent = g('z').toFixed(2)
  wrapper.scale.setScalar(s)
  wrapper.position.set(g('x'), g('y'), g('z'))
  avatar?.getRenderer()?.render()
}
for (const id of Object.values(T)) document.getElementById(id).addEventListener('input', applyTransform)
document.getElementById('t_reset').addEventListener('click', () => {
  document.getElementById('t_scale').value = 1
  for (const k of ['x','y','z']) document.getElementById(k === 'x' ? 't_x' : k === 'y' ? 't_y' : 't_z').value = 0
  applyTransform(); setStatus('已重置位置/缩放')
})

// ---------------- MediaPipe ----------------
async function ensureLandmarker() {
  if (landmarker) return landmarker
  setStatus('初始化 MediaPipe…')
  const vision = await FilesetResolver.forVisionTasks(WASM)
  const opts = (delegate) => ({
    baseOptions: { modelAssetPath: MODEL, delegate },
    outputFaceBlendshapes: true, outputFacialTransformationMatrixes: true,
    runningMode: 'VIDEO', numFaces: 1
  })
  try { landmarker = await FaceLandmarker.createFromOptions(vision, opts('GPU')) }
  catch (e) { console.warn('GPU 失败，回退 CPU', e); landmarker = await FaceLandmarker.createFromOptions(vision, opts('CPU')) }
  return landmarker
}

// ---------------- 摄像头 ----------------
document.getElementById('start').addEventListener('click', async () => {
  const btn = document.getElementById('start'); btn.disabled = true
  const problem = cameraProblem()
  if (problem) { setStatus('摄像头失败: ' + problem); btn.disabled = false; return }
  try {
    setStatus('请求摄像头权限…')
    camStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }, audio: false
    })
    video.srcObject = camStream
    await new Promise(r => { if (video.readyState >= 1) r(); else video.onloadedmetadata = r })
    await video.play()
    await ensureAvatar()
    const lk = await ensureLandmarker()
    playing = true; setStatus('摄像头运行中 ✅'); btn.textContent = '运行中'
    const loop = () => {
      if (!playing) return
      const r = lk.detectForVideo(video, performance.now())
      if (r?.faceLandmarks?.length) avatar.processLandmarkData(r)
      requestAnimationFrame(loop)
    }
    loop()
  } catch (e) {
    const map = { NotAllowedError: '用户/系统拒绝了摄像头权限', NotFoundError: '找不到摄像头设备',
                  NotReadableError: '摄像头被其他程序占用', OverconstrainedError: '不支持所请求的分辨率' }
    setStatus('摄像头失败: ' + (map[e?.name] || e?.name || '') + ' — ' + (e?.message || e))
    btn.disabled = false
  }
})

// ---------------- 文件模式 ----------------
function stopFile() { playing = false; video.pause(); if (camStream) { camStream.getTracks().forEach(t => t.stop()); camStream = null } }
document.getElementById('stopFile').addEventListener('click', () => { stopFile(); setStatus('已停止') })

async function runOnElement(el, isVideo) {
  await ensureAvatar()
  const lk = await ensureLandmarker()
  if (isVideo) {
    playing = true
    const loop = () => {
      if (!playing || video.paused || video.ended) { setStatus('播放结束'); return }
      const r = lk.detectForVideo(video, performance.now())
      if (r?.faceLandmarks?.length) avatar.processLandmarkData(r)
      requestAnimationFrame(loop)
    }
    loop()
  } else {
    lk.setOptions({ runningMode: 'IMAGE' })
    const r = lk.detect(el)
    lk.setOptions({ runningMode: 'VIDEO' })
    if (r?.faceLandmarks?.length) { avatar.processLandmarkData(r); setStatus('图片已应用 ✅（静态，中性表情）') }
    else setStatus('图片里没检测到人脸')
  }
}
document.getElementById('file').addEventListener('change', async (ev) => {
  const f = ev.target.files?.[0]; if (!f) return
  stopFile()
  const url = URL.createObjectURL(f)
  if (f.type.startsWith('video')) {
    video.srcObject = null; video.src = url; video.loop = false; frame.src = ''
    await new Promise(r => { video.onloadedmetadata = r })
    await video.play(); setStatus('播放视频中…'); runOnElement(video, true)
  } else {
    frame.src = url; video.src = ''
    await new Promise(r => { frame.onload = r }); setStatus('处理图片…'); runOnElement(frame, false)
  }
})
document.getElementById('playSample').addEventListener('click', async () => {
  stopFile(); video.src = ''; video.srcObject = null
  frame.src = '/sample.jpg'
  await new Promise(r => { frame.onload = r }); setStatus('处理内置样例…'); runOnElement(frame, false)
})

// ---------------- 手动表情 ----------------
const SP = { jaw:'s_jaw', blink:'s_blink', smile:'s_smile', brow:'s_brow', tongue:'s_tongue', yaw:'s_yaw' }
const MAP = { jaw:'jawOpen', blink:'eyeBlinkLeft', smile:'mouthSmileLeft', brow:'browInnerUp', tongue:'tongueOut' }
async function onSlider() {
  await ensureAvatar()
  const a = avatar.getRenderer()?.getAvatar(); if (!a) return
  const m = new Map()
  for (const k of ['jaw','blink','smile','brow','tongue']) {
    const v = parseFloat(document.getElementById(SP[k]).value)
    document.getElementById('v_' + k).textContent = v.toFixed(2)
    m.set(MAP[k], v)
  }
  a.updateBlendshapes(m)
  const yaw = parseFloat(document.getElementById(SP.yaw).value)
  document.getElementById('v_yaw').textContent = yaw.toFixed(2)
  const scene = a.getScene()
  if (scene) { scene.matrixAutoUpdate = true; scene.rotation.y = yaw * 0.6; scene.updateMatrix() }
  avatar.getRenderer().render()
}
for (const id of Object.values(SP)) document.getElementById(id).addEventListener('input', onSlider)
