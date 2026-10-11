import { Aniface } from 'aniface'
import * as THREE from 'three'
import { FaceLandmarker, FilesetResolver, DrawingUtils } from '@mediapipe/tasks-vision'

const WASM  = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm'
const MODEL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'

const canvas   = document.getElementById('avatar')
const video    = document.getElementById('webcam')
const overlay  = document.getElementById('overlay')
const octx     = overlay.getContext('2d')
const drawUtils = new DrawingUtils(octx)
const frame    = document.getElementById('frame')
const wrap     = document.getElementById('videowrap')
const statusEl = document.getElementById('status')
const setStatus = (t) => { statusEl.textContent = t; console.log('[status]', t) }
const $ = (id) => document.getElementById(id)

let avatar = null, landmarker = null, camStream = null, playing = false, wrapper = null
let mode = 'idle'          // idle | camera | file

// ---------------- 环境自检 ----------------
function cameraProblem() {
  if (!window.isSecureContext) return '当前不是「安全上下文」，摄像头 API 只在 https:// 或 http://localhost 下可用。你现在访问的是 ' + location.origin
  if (!navigator.mediaDevices) return 'navigator.mediaDevices 不存在（浏览器过旧，或页面在受限 iframe 里）'
  if (!navigator.mediaDevices.getUserMedia) return '浏览器不支持 getUserMedia'
  return null
}
window.addEventListener('DOMContentLoaded', () => {
  $('diag').textContent = 'origin=' + location.origin + ' · secure=' + window.isSecureContext + ' · mediaDevices=' + !!navigator.mediaDevices
  const p = cameraProblem(); if (p) setStatus('⚠️ ' + p)
})

// ---------------- 3D 模型 ----------------
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
function ensureWrapper() {
  if (wrapper || !avatar) return
  const inner = avatar.getRenderer()?.getAvatar()?.getScene()
  if (!inner || !inner.parent) return
  wrapper = new THREE.Group(); inner.parent.add(wrapper); wrapper.add(inner)
  wrapper.position.set(0,0,0); wrapper.scale.setScalar(1)
}

// ---------------- 关键点叠加 + 实时信息 ----------------
const S = { frames:0, t0:performance.now(), fps:0, lastDetect:0 }
function fitOverlay() {
  const w = video.videoWidth, h = video.videoHeight
  if (w && h && (overlay.width !== w || overlay.height !== h)) {
    overlay.width = w; overlay.height = h
    octx.lineCap = 'round'; octx.lineJoin = 'round'
    $('s_res').textContent = w + '×' + h
  }
}
function drawOverlay(results, keepBg) {
  if (!keepBg) octx.clearRect(0, 0, overlay.width, overlay.height)
  if (!results?.faceLandmarks?.length) return
  const showLm = $('c_lm').checked, showMesh = $('c_mesh').checked
  for (const lm of results.faceLandmarks) {
    if (showMesh) drawUtils.drawConnectors(lm, FaceLandmarker.FACE_LANDMARKS_TESSELATION, { color:'#2ee66b44', lineWidth:1 })
    if (showLm) {
      drawUtils.drawConnectors(lm, FaceLandmarker.FACE_LANDMARKS_FACE_OVAL,   { color:'#ffffffcc', lineWidth:2 })
      drawUtils.drawConnectors(lm, FaceLandmarker.FACE_LANDMARKS_LIPS,        { color:'#ff7ab6dd', lineWidth:2 })
      drawUtils.drawConnectors(lm, FaceLandmarker.FACE_LANDMARKS_LEFT_EYE,    { color:'#ffd166',   lineWidth:2 })
      drawUtils.drawConnectors(lm, FaceLandmarker.FACE_LANDMARKS_RIGHT_EYE,   { color:'#66d9ff',   lineWidth:2 })
      drawUtils.drawConnectors(lm, FaceLandmarker.FACE_LANDMARKS_LEFT_EYEBROW,{ color:'#ffd16699', lineWidth:1 })
      drawUtils.drawConnectors(lm, FaceLandmarker.FACE_LANDMARKS_RIGHT_EYEBROW,{ color:'#66d9ff99',lineWidth:1 })
      drawUtils.drawLandmarks(lm, { color:'#ffffff77', radius:1 })
    }
  }
}
function updateStats(results) {
  const now = performance.now()
  S.frames++
  if (now - S.t0 >= 500) { S.fps = S.frames * 1000 / (now - S.t0); S.frames = 0; S.t0 = now }
  $('s_fps').textContent  = S.fps.toFixed(1) + ' fps'
  $('s_lat').textContent  = S.lastDetect.toFixed(0) + ' ms'
  const has = !!(results?.faceLandmarks?.length)
  $('s_face').innerHTML   = has ? '<span class="ok">检测到</span>' : '<span class="no">未检测</span>'
  $('s_pts').textContent  = has ? results.faceLandmarks[0].length + ' 点' : '-'
}
function resetStats() {
  for (const k of ['fps','lat','face','pts']) $('s_' + k).textContent = (k==='face') ? '-' : '-'
  $('s_res').textContent = '-'
}
function detect(lk, el, ts) {
  const t = performance.now()
  const r = lk.detectForVideo(el, ts)
  S.lastDetect = performance.now() - t
  return r
}

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

// ---------------- 控制项 ----------------
$('c_mirror').addEventListener('change', (e) => wrap.classList.toggle('mirror', e.target.checked))

// ---------------- 摄像头 ----------------
$('start').addEventListener('click', async () => {
  const btn = $('start'); btn.disabled = true
  const problem = cameraProblem()
  if (problem) { setStatus('摄像头失败: ' + problem); btn.disabled = false; return }
  try {
    setStatus('请求摄像头权限…')
    camStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' }, audio: false
    })
    video.srcObject = camStream
    await new Promise(r => { if (video.readyState >= 1) r(); else video.onloadedmetadata = r })
    await video.play()
    fitOverlay()
    const tr = camStream.getVideoTracks()[0]
    const st = tr.getSettings ? tr.getSettings() : {}
    $('s_dev').textContent = (tr.label || st.deviceId || 'camera')
    await ensureAvatar()
    const lk = await ensureLandmarker()
    playing = true; mode = 'camera'
    setStatus('摄像头运行中 ✅'); btn.textContent = '运行中'
    const loop = () => {
      if (!playing || mode !== 'camera') return
      const r = detect(lk, video, performance.now())
      if (r?.faceLandmarks?.length) avatar.processLandmarkData(r)
      fitOverlay(); drawOverlay(r); updateStats(r)
      requestAnimationFrame(loop)
    }
    loop()
  } catch (e) {
    const map = { NotAllowedError:'用户/系统拒绝了摄像头权限', NotFoundError:'找不到摄像头设备',
                  NotReadableError:'摄像头被其他程序占用', OverconstrainedError:'不支持所请求的分辨率' }
    setStatus('摄像头失败: ' + (map[e?.name] || e?.name || '') + ' — ' + (e?.message || e))
    btn.disabled = false
  }
})
$('stopCam').addEventListener('click', () => {
  playing = false; mode = 'idle'
  if (camStream) { camStream.getTracks().forEach(t => t.stop()); camStream = null }
  video.srcObject = null
  octx.clearRect(0,0,overlay.width,overlay.height)
  resetStats(); $('s_dev').textContent = '-'
  $('start').disabled = false; $('start').textContent = '启动摄像头'
  setStatus('摄像头已停止')
})

// ---------------- 文件模式 ----------------
function stopFile() {
  playing = false; mode = 'idle'
  video.pause()
  octx.clearRect(0,0,overlay.width,overlay.height)
}
$('stopFile').addEventListener('click', () => { stopFile(); setStatus('已停止') })

async function runOnElement(el, isVideo) {
  await ensureAvatar()
  const lk = await ensureLandmarker()
  if (isVideo) {
    playing = true; mode = 'file'
    const loop = () => {
      if (!playing || mode !== 'file' || video.paused || video.ended) { if (mode==='file') setStatus('播放结束'); return }
      const r = detect(lk, video, performance.now())
      if (r?.faceLandmarks?.length) avatar.processLandmarkData(r)
      fitOverlay(); drawOverlay(r); updateStats(r)
      requestAnimationFrame(loop)
    }
    loop()
  } else {
    overlay.width = el.naturalWidth || el.width; overlay.height = el.naturalHeight || el.height
    $('s_res').textContent = overlay.width + '×' + overlay.height
    lk.setOptions({ runningMode: 'IMAGE' })
    const r = lk.detect(el)
    lk.setOptions({ runningMode: 'VIDEO' })
    octx.drawImage(el, 0, 0, overlay.width, overlay.height)   // 图片画进摄像头面板
    drawOverlay(r, true); updateStats(r)
    if (r?.faceLandmarks?.length) { avatar.processLandmarkData(r); setStatus('图片已应用 ✅（静态，中性表情）') }
    else setStatus('图片里没检测到人脸')
  }
}
$('file').addEventListener('change', async (ev) => {
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
$('playSample').addEventListener('click', async () => {
  stopFile(); video.src = ''; video.srcObject = null
  frame.src = '/sample.jpg'
  await new Promise(r => { frame.onload = r }); setStatus('处理内置样例…'); runOnElement(frame, false)
})

// ---------------- 位置 / 缩放 ----------------
const T = ['t_scale','t_x','t_y','t_z']
function applyTransform() {
  if (!wrapper) return
  const g = (id) => parseFloat($(id).value)
  const s = g('t_scale')
  $('tv_scale').textContent = s.toFixed(2)
  $('tv_x').textContent = g('t_x').toFixed(2)
  $('tv_y').textContent = g('t_y').toFixed(2)
  $('tv_z').textContent = g('t_z').toFixed(2)
  wrapper.scale.setScalar(s)
  wrapper.position.set(g('t_x'), g('t_y'), g('t_z'))
  avatar?.getRenderer()?.render()
}
for (const id of T) $(id).addEventListener('input', applyTransform)
$('t_reset').addEventListener('click', () => {
  $('t_scale').value = 1; $('t_x').value = 0; $('t_y').value = 0; $('t_z').value = 0
  applyTransform(); setStatus('已重置位置/缩放')
})

// ---------------- 手动表情 ----------------
const SP  = { jaw:'s_jaw', blink:'s_blink', smile:'s_smile', brow:'s_brow', tongue:'s_tongue', yaw:'s_yaw' }
const MAP = { jaw:'jawOpen', blink:'eyeBlinkLeft', smile:'mouthSmileLeft', brow:'browInnerUp', tongue:'tongueOut' }
async function onSlider() {
  await ensureAvatar()
  const a = avatar.getRenderer()?.getAvatar(); if (!a) return
  const m = new Map()
  for (const k of ['jaw','blink','smile','brow','tongue']) {
    const v = parseFloat($(SP[k]).value)
    $('v_' + k).textContent = v.toFixed(2)
    m.set(MAP[k], v)
  }
  a.updateBlendshapes(m)
  const yaw = parseFloat($(SP.yaw).value)
  $('v_yaw').textContent = yaw.toFixed(2)
  const sc = a.getScene()
  if (sc) { sc.matrixAutoUpdate = true; sc.rotation.y = yaw * 0.6; sc.updateMatrix() }
  avatar.getRenderer().render()
}
for (const id of Object.values(SP)) $(id).addEventListener('input', onSlider)


