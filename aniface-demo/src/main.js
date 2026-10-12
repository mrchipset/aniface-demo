import { Aniface } from 'aniface'
import * as THREE from 'three'
import { FaceLandmarker, ImageSegmenter, FilesetResolver, DrawingUtils } from '@mediapipe/tasks-vision'

// MediaPipe 运行时来源：本地优先（npm run vendor:mediapipe 后可用），失败再退回 CDN
const SOURCES = [
  { name: '本地', wasm: '/mediapipe/wasm', model: '/mediapipe/face_landmarker.task',
                  seg: '/mediapipe/selfie_segmenter.tflite' },
  { name: 'CDN',  wasm: 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm',
                  model: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
                  seg: 'https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/1/selfie_segmenter.tflite' },
]

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
const on = (id, ev, fn) => { const e = $(id); if (e) e.addEventListener(ev, fn) }   // 元素可能已被移除

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
  const opts = (src, delegate) => ({
    baseOptions: { modelAssetPath: src.model, delegate },
    outputFaceBlendshapes: true, outputFacialTransformationMatrixes: true,
    runningMode: 'VIDEO', numFaces: 1
  })
  let lastErr = null
  for (const src of SOURCES) {
    for (const delegate of ['GPU', 'CPU']) {
      try {
        setStatus(`初始化 MediaPipe（${src.name} / ${delegate}）…`)
        const vision = await FilesetResolver.forVisionTasks(src.wasm)
        landmarker = await FaceLandmarker.createFromOptions(vision, opts(src, delegate))
        console.log('[mediapipe] 就绪:', src.name, delegate)
        return landmarker
      } catch (e) {
        lastErr = e
        console.warn(`[mediapipe] ${src.name}/${delegate} 失败:`, e?.message || e)
      }
    }
  }
  throw new Error('MediaPipe 初始化失败（本地与 CDN 都不可用）: ' + (lastErr?.message || lastErr))
}

// ---------------- 控制项 ----------------
$('c_mirror').addEventListener('change', (e) => { wrap.classList.toggle('mirror', e.target.checked); compositeRefresh() })

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
    if ($('cp_hint')) $('cp_hint').textContent = '已就绪'
    const loop = () => {
      if (!playing || mode !== 'camera') return
      const r = detect(lk, video, performance.now())
      tickSegmentation(video, performance.now())
      stepAvatar(r)
      fitOverlay(); drawOverlay(r); updateStats(r)
      drawComposite(video, r?.faceLandmarks?.[0], video.videoWidth, video.videoHeight)
      drawOutput(); drawSelectionOverlay()
      lastComp = { srcEl: video, lms: r?.faceLandmarks?.[0], w: video.videoWidth, h: video.videoHeight }
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
  if (cctx) cctx.clearRect(0, 0, comp.width, comp.height)
  lastComp = null
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
      tickSegmentation(video, performance.now())
      stepAvatar(r)
      fitOverlay(); drawOverlay(r); updateStats(r)
      drawComposite(video, r?.faceLandmarks?.[0], video.videoWidth, video.videoHeight)
      drawOutput(); drawSelectionOverlay()
      lastComp = { srcEl: video, lms: r?.faceLandmarks?.[0], w: video.videoWidth, h: video.videoHeight }
      requestAnimationFrame(loop)
    }
    loop()
  } else {
    overlay.width = el.naturalWidth || el.width; overlay.height = el.naturalHeight || el.height
    $('s_res').textContent = overlay.width + '×' + overlay.height
    lk.setOptions({ runningMode: 'IMAGE' })
    const r = lk.detect(el)
    lk.setOptions({ runningMode: 'VIDEO' })
    // 图片模式也跑一次分割（虚化对静态图同样生效）
    const bOnEl = $('blur_on')
    if (bOnEl && bOnEl.checked && segmenter) {
      try {
        segmenter.setOptions({ runningMode: 'IMAGE' })
        const sr = segmenter.segment(el)
        hasMask = updateMaskCanvas(sr)
        if (sr && sr.close) sr.close()
        segmenter.setOptions({ runningMode: 'VIDEO' })
      } catch (e) { console.warn('[segmenter] 图片分割失败:', e?.message || e) }
    }
    octx.drawImage(el, 0, 0, overlay.width, overlay.height)   // 图片画进摄像头面板
    drawOverlay(r, true); updateStats(r)
    if (r?.faceLandmarks?.length) {
      stepAvatar(r)
      drawComposite(el, r.faceLandmarks[0], el.naturalWidth || el.width, el.naturalHeight || el.height)
      drawOutput(); drawSelectionOverlay()
      lastComp = { srcEl: el, lms: r.faceLandmarks[0], w: el.naturalWidth || el.width, h: el.naturalHeight || el.height }
      setStatus('图片已应用 ✅（静态，中性表情）')
    }
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
// ---------------- 合成：把小熊猫贴进摄像头画面 ----------------
const comp = document.getElementById('composite')
const cctx = comp ? comp.getContext('2d') : null
let lastComp = null      // { srcEl, lms, w, h }：拖动滑块时用来重绘
let cpTick = 0           // 诊断输出节流

function cpLabels() {
  if (!$('cp_size')) return
  $('cpv_size').textContent = parseFloat($('cp_size').value).toFixed(2)
  $('cpv_dx').textContent   = parseFloat($('cp_dx').value).toFixed(2)
  $('cpv_dy').textContent   = parseFloat($('cp_dy').value).toFixed(2)
}

// ---------------- 输出视图：选区裁剪 × 倍率 ----------------
const outCv = document.getElementById('output')
let sel = { w: 400, h: 400, cx: 0.5, cy: 0.5, mul: 1, mask: 'none', radius: 18, feather: 0 }
let maskShapeCv = null, maskShapeCtx = null
let selDragging = false

function selLabels() {
  if (!$('selv_w')) return
  $('selv_w').textContent = Math.round(sel.w)
  $('selv_h').textContent = Math.round(sel.h)
  $('selv_x').textContent = sel.cx.toFixed(2)
  $('selv_y').textContent = sel.cy.toFixed(2)
  $('selv_mul').textContent = sel.mul.toFixed(2)
  const maskName = { none: '无', round: '圆角', circle: '圆形' }[sel.mask] || '无'
  if ($('selv_mask')) $('selv_mask').textContent = maskName
  if ($('selv_radius')) $('selv_radius').textContent = Math.round(sel.radius) + '%'
  if ($('selv_feather')) $('selv_feather').textContent = Math.round(sel.feather)
  $('sel_info').textContent = `${Math.round(sel.w)}×${Math.round(sel.h)} → ${Math.round(sel.w * sel.mul)}×${Math.round(sel.h * sel.mul)}` + (sel.mask !== 'none' ? ` · ${maskName}` : '')
}

function selFromUI() {
  if (!$('sel_w')) return
  sel.w = parseFloat($('sel_w').value)
  sel.h = parseFloat($('sel_h').value)
  sel.cx = parseFloat($('sel_x').value)
  sel.cy = parseFloat($('sel_y').value)
  sel.mul = parseFloat($('sel_mul').value)
  if ($('sel_mask')) sel.mask = $('sel_mask').value
  if ($('sel_radius')) sel.radius = parseFloat($('sel_radius').value)
  if ($('sel_feather')) sel.feather = parseFloat($('sel_feather').value)
  selLabels()
}
function selToUI() {
  if (!$('sel_w')) return
  $('sel_w').value = sel.w; $('sel_h').value = sel.h
  $('sel_x').value = sel.cx; $('sel_y').value = sel.cy
  $('sel_mul').value = sel.mul
  if ($('sel_mask')) $('sel_mask').value = sel.mask
  if ($('sel_radius')) $('sel_radius').value = sel.radius
  if ($('sel_feather')) $('sel_feather').value = sel.feather
  selLabels()
}

// 选区矩形（合成画布像素坐标，左上角）
function selRect(cw, ch) {
  const w = Math.min(sel.w, cw), h = Math.min(sel.h, ch)
  let x = sel.cx * cw - w / 2
  let y = sel.cy * ch - h / 2
  x = Math.max(0, Math.min(cw - w, x))
  y = Math.max(0, Math.min(ch - h, y))
  return { x: Math.round(x), y: Math.round(y), w: Math.round(w), h: Math.round(h) }
}

// ---- 蒙版：圆角矩形 / 圆形（带边缘羽化）----
function maskPath(ctx, w, h, shape, radiusPct) {
  ctx.beginPath()
  if (shape === 'circle') {
    ctx.ellipse(w / 2, h / 2, w / 2, h / 2, 0, 0, Math.PI * 2)
  } else {
    const r = Math.max(0, Math.min(w, h) * (radiusPct / 100) / 2) * 2
    const rr = Math.min(r, Math.min(w, h) / 2)
    if (rr <= 0.5) { ctx.rect(0, 0, w, h); return }
    if (ctx.roundRect) { ctx.roundRect(0, 0, w, h, rr); return }
    // 兼容老浏览器：手工圆角路径
    ctx.moveTo(rr, 0)
    ctx.lineTo(w - rr, 0); ctx.quadraticCurveTo(w, 0, w, rr)
    ctx.lineTo(w, h - rr); ctx.quadraticCurveTo(w, h, w - rr, h)
    ctx.lineTo(rr, h);     ctx.quadraticCurveTo(0, h, 0, h - rr)
    ctx.lineTo(0, rr);     ctx.quadraticCurveTo(0, 0, rr, 0)
    ctx.closePath()
  }
}

function applyOutputMask(c, ow, oh) {
  if (!sel.mask || sel.mask === 'none') return
  if (!maskShapeCv) { maskShapeCv = document.createElement('canvas'); maskShapeCtx = maskShapeCv.getContext('2d') }
  if (maskShapeCv.width !== ow || maskShapeCv.height !== oh) { maskShapeCv.width = ow; maskShapeCv.height = oh }
  const m = maskShapeCtx
  m.setTransform(1, 0, 0, 1, 0, 0)
  m.clearRect(0, 0, ow, oh)
  m.save()
  if (sel.feather > 0) m.filter = 'blur(' + sel.feather + 'px)'
  m.fillStyle = '#fff'
  maskPath(m, ow, oh, sel.mask, sel.radius)
  m.fill()
  m.restore()
  c.globalCompositeOperation = 'destination-in'
  c.drawImage(maskShapeCv, 0, 0)
  c.globalCompositeOperation = 'source-over'
}

// 把合成画布的选区裁剪出来，按倍率画到输出画布
function drawOutput() {
  if (!outCv || !comp) return
  const r = selRect(comp.width, comp.height)
  const ow = Math.max(1, Math.round(r.w * sel.mul))
  const oh = Math.max(1, Math.round(r.h * sel.mul))
  if (outCv.width !== ow || outCv.height !== oh) { outCv.width = ow; outCv.height = oh }
  const c = outCv.getContext('2d')
  c.setTransform(1, 0, 0, 1, 0, 0)
  c.clearRect(0, 0, ow, oh)
  c.imageSmoothingEnabled = true
  c.imageSmoothingQuality = 'high'
  c.drawImage(comp, r.x, r.y, r.w, r.h, 0, 0, ow, oh)
  applyOutputMask(c, ow, oh)
}

// 在合成视图上画出选区（半透明遮罩 + 虚线框 + 尺寸标注）
function drawSelectionOverlay() {
  if (!comp || !cctx) return
  const r = selRect(comp.width, comp.height)
  cctx.save()
  cctx.fillStyle = 'rgba(0,0,0,0.38)'
  cctx.beginPath()
  cctx.rect(0, 0, comp.width, comp.height)
  cctx.rect(r.x, r.y, r.w, r.h)
  cctx.fill('evenodd')
  cctx.strokeStyle = '#4f7cff'
  cctx.lineWidth = Math.max(2, comp.width / 500)
  cctx.setLineDash([10, 6])
  cctx.strokeRect(r.x, r.y, r.w, r.h)
  cctx.setLineDash([])
  cctx.fillStyle = '#4f7cff'
  cctx.font = 'bold ' + Math.max(14, comp.width / 45) + 'px system-ui,sans-serif'
  cctx.fillText(Math.round(r.w) + '×' + Math.round(r.h) + ' → ' + Math.round(r.w * sel.mul) + '×' + Math.round(r.h * sel.mul),
                r.x + 6, Math.max(20, r.y - 8))
  cctx.restore()
}

// 在合成视图上拖拽移动选区
function selMoveTo(ev) {
  const rect = comp.getBoundingClientRect()
  if (!rect.width || !rect.height) return
  sel.cx = Math.min(1, Math.max(0, (ev.clientX - rect.left) / rect.width))
  sel.cy = Math.min(1, Math.max(0, (ev.clientY - rect.top) / rect.height))
  selToUI()
  compositeRefresh()
}
if (comp) {
  comp.style.cursor = 'crosshair'
  comp.addEventListener('pointerdown', (e) => { selDragging = true; comp.setPointerCapture(e.pointerId); selMoveTo(e) })
  comp.addEventListener('pointermove', (e) => { if (selDragging) selMoveTo(e) })
  comp.addEventListener('pointerup',   (e) => { selDragging = false })
  comp.addEventListener('pointercancel', () => { selDragging = false })
}

for (const id of ['sel_w','sel_h','sel_x','sel_y','sel_mul','sel_mask','sel_radius','sel_feather']) {
  on(id, 'input', () => { selFromUI(); compositeRefresh() })
}
if ($('sel_reset')) $('sel_reset').addEventListener('click', () => {
  sel = { w: 400, h: 400, cx: 0.5, cy: 0.5, mul: 1 }
  selToUI(); compositeRefresh(); setStatus('已重置输出选区')
})
selToUI()

// ---------------- 背景虚化（Selfie Segmenter + 2D 合成） ----------------
let segmenter = null, segTried = false, hasMask = false, segTick = 0
let offA = null, offB = null, offC = null, maskCanvas = null, maskCtx = null

async function ensureSegmenter() {
  if (segmenter || segTried) return segmenter
  segTried = true
  for (const src of SOURCES) {
    for (const delegate of ['GPU', 'CPU']) {
      try {
        const vision = await FilesetResolver.forVisionTasks(src.wasm)
        segmenter = await ImageSegmenter.createFromOptions(vision, {
          baseOptions: { modelAssetPath: src.seg, delegate },
          runningMode: 'VIDEO',
          outputConfidenceMasks: true,
          outputCategoryMask: false
        })
        segInfo.state = '就绪'; segInfo.delegate = delegate
        console.log('[segmenter] 就绪:', src.name, delegate)
        setStatus('背景虚化已就绪 ✅')
        return segmenter
      } catch (e) {
        console.warn('[segmenter] ' + src.name + '/' + delegate + ' 失败:', e?.message || e)
      }
    }
  }
  segInfo.state = '加载失败'
  setStatus('⚠️ 背景虚化不可用（分割模型加载失败）')
  return null
}

function ensureOffscreens(w, h) {
  if (!offA) { offA = document.createElement('canvas'); offA._c = offA.getContext('2d') }
  if (!offB) { offB = document.createElement('canvas'); offB._c = offB.getContext('2d') }
  if (!offC) { offC = document.createElement('canvas'); offC._c = offC.getContext('2d') }
  if (!maskCanvas) { maskCanvas = document.createElement('canvas'); maskCtx = maskCanvas.getContext('2d', { willReadFrequently: true }) }
  for (const c of [offA, offB, offC]) if (c.width !== w || c.height !== h) { c.width = w; c.height = h }
}

// 分割结果 -> alpha 遮罩画布（人物=不透明）
let segInfo = { state: '未加载', delegate: '', personPct: 0, kind: '' }

function updateMaskCanvas(res) {
  if (!res) return false
  if (!maskCanvas) { maskCanvas = document.createElement('canvas'); maskCtx = maskCanvas.getContext('2d', { willReadFrequently: true }) }
  // selfie_segmenter 多数情况只给 categoryMask（0/1），部分版本给 confidenceMasks（0..1）
  let arr = null, mw = 0, mh = 0, isCat = false
  if (res.confidenceMasks && res.confidenceMasks.length) {
    const m = res.confidenceMasks[0]
    mw = m.width; mh = m.height; arr = m.getAsFloat32Array(); segInfo.kind = 'confidence'
  } else if (res.categoryMask) {
    const m = res.categoryMask
    mw = m.width; mh = m.height; arr = m.getAsUint8Array(); isCat = true; segInfo.kind = 'category'
  }
  if (!arr) { segInfo.kind = 'none'; return false }
  if (maskCanvas.width !== mw || maskCanvas.height !== mh) { maskCanvas.width = mw; maskCanvas.height = mh }
  const img = maskCtx.createImageData(mw, mh)
  const invEl = $('blur_invert')
  const inv = invEl ? invEl.checked : false
  let person = 0
  for (let i = 0; i < mw * mh; i++) {
    let a = isCat ? (arr[i] > 0 ? 1 : 0) : arr[i]
    if (inv) a = 1 - a
    person += a
    img.data[i * 4] = 255; img.data[i * 4 + 1] = 255; img.data[i * 4 + 2] = 255
    img.data[i * 4 + 3] = Math.max(0, Math.min(1, a)) * 255
  }
  segInfo.personPct = Math.round(100 * person / (mw * mh))
  maskCtx.putImageData(img, 0, 0)
  return true
}

// 每帧（节流）跑一次分割；仅在开启虚化时才跑，省算力
function tickSegmentation(srcEl, ts) {
  const onEl = $('blur_on')
  if (!onEl || !onEl.checked || !segmenter) return
  if ((segTick++ % 2) !== 0) return
  try {
    const res = segmenter.segmentForVideo(srcEl, ts)
    hasMask = updateMaskCanvas(res)
    if (res && res.close) res.close()
    if ((segTick % 20) === 0) blurDiag()
  } catch (e) {
    console.warn('[segmenter] segment 失败:', e?.message || e)
  }
}

function blurDiag() {
  const el = $('blur_dbg'); if (!el) return
  const onEl = $('blur_on')
  el.textContent = '分割=' + segInfo.state + (segInfo.delegate ? '(' + segInfo.delegate + ')' : '')
    + ' · 遮罩=' + (hasMask ? '有/' + segInfo.kind + '/人物' + segInfo.personPct + '%' : '无')
    + ' · 虚化=' + ($('blur_px') ? $('blur_px').value : '?') + 'px'
    + ' · 开关=' + (onEl ? (onEl.checked ? '开' : '关') : '缺')
}

// 把视频画进合成画布：可选背景虚化（底层模糊 + 上层人物抠图）
function drawVideoLayer(srcEl, w, h, mirrorL, blurOn, blurPx) {
  if (!blurOn || !hasMask) {
    cctx.save()
    if (mirrorL) { cctx.translate(w, 0); cctx.scale(-1, 1) }
    cctx.drawImage(srcEl, 0, 0, w, h)
    cctx.restore()
    return
  }
  ensureOffscreens(w, h)
  const a = offA._c, b = offB._c, c = offC._c
  // A: 原始画面（按需镜像）
  a.setTransform(1, 0, 0, 1, 0, 0); a.clearRect(0, 0, w, h)
  if (mirrorL) { a.translate(w, 0); a.scale(-1, 1) }
  a.drawImage(srcEl, 0, 0, w, h)
  // B: 模糊版（放大一点画，避免边缘出现透明描边）
  b.setTransform(1, 0, 0, 1, 0, 0); b.clearRect(0, 0, w, h)
  b.save()
  b.filter = 'blur(' + blurPx + 'px)'
  const pad = blurPx * 2
  b.drawImage(offA, -pad, -pad, w + pad * 2, h + pad * 2)
  b.restore()
  // C: 人物抠图（原图 + 遮罩；镜像时遮罩也要一起翻）
  c.setTransform(1, 0, 0, 1, 0, 0); c.clearRect(0, 0, w, h)
  c.drawImage(offA, 0, 0)
  c.globalCompositeOperation = 'destination-in'
  c.save()
  if (mirrorL) { c.translate(w, 0); c.scale(-1, 1) }
  c.imageSmoothingEnabled = true
  c.drawImage(maskCanvas, 0, 0, w, h)
  c.restore()
  c.globalCompositeOperation = 'source-over'
  // 合成：模糊背景 + 清晰人物
  cctx.drawImage(offB, 0, 0)
  cctx.drawImage(offC, 0, 0)
}

function drawComposite(srcEl, landmarks, srcW, srcH) {
  if (!comp || !cctx || !srcW || !srcH) return
  if (comp.width !== srcW || comp.height !== srcH) { comp.width = srcW; comp.height = srcH }
  const mirror = $('c_mirror') ? $('c_mirror').checked : true
  cctx.setTransform(1, 0, 0, 1, 0, 0)
  cctx.clearRect(0, 0, comp.width, comp.height)

  // ① 底层：原始画面（可选背景虚化）
  const blurOnEl = $('blur_on')
  const blurOn = blurOnEl ? blurOnEl.checked : false
  const blurPx = $('blur_px') ? parseFloat($('blur_px').value) : 14
  drawVideoLayer(srcEl, comp.width, comp.height, mirror, blurOn, blurPx)

  const cpOn = $('cp_on') ? $('cp_on').checked : true
  if (!cpOn || !landmarks || !landmarks.length) return

  // ② 人脸框 -> 整个头（关键点只覆盖面部，向上多留头顶/头发）
  let x0 = 1, y0 = 1, x1 = 0, y1 = 0
  for (const p of landmarks) {
    if (p.x < x0) x0 = p.x; if (p.x > x1) x1 = p.x
    if (p.y < y0) y0 = p.y; if (p.y > y1) y1 = p.y
  }
  const fw = x1 - x0, fh = y1 - y0
  const bx0 = x0 - fw * 0.32, bx1 = x1 + fw * 0.32
  const by0 = y0 - fh * 0.62, by1 = y1 + fh * 0.18

  const k  = parseFloat($('cp_size').value)
  const bh = (by1 - by0) * comp.height * k
  let cxn = (bx0 + bx1) / 2
  if (mirror) cxn = 1 - cxn      // 画面镜像时，人脸框 x 必须一起翻转
  const cx = cxn * comp.width + parseFloat($('cp_dx').value) * comp.width
  const cy = ((by0 + by1) / 2) * comp.height + parseFloat($('cp_dy').value) * comp.height

  // ③ 顶层：模型画布（透明背景）；按高度贴合，宽度等比
  const av = canvas
  const ww = bh * (av.width / av.height)
  const dx = cx - ww / 2, dy = cy - bh / 2
  if ((cpTick++ % 15) === 0 && $('cp_dbg')) {
    $('cp_dbg').textContent =
      `脸框[${x0.toFixed(2)},${y0.toFixed(2)}→${x1.toFixed(2)},${y1.toFixed(2)}] `
      + `大小${k.toFixed(2)} 偏移X${parseFloat($('cp_dx').value).toFixed(2)} 偏移Y${parseFloat($('cp_dy').value).toFixed(2)} `
      + `| 贴到 (${Math.round(dx)},${Math.round(dy)}) ${Math.round(ww)}x${Math.round(bh)} 画布${comp.width}x${comp.height} 镜像${mirror}`
  }
  cctx.save()
  cctx.imageSmoothingEnabled = true
  // aniface 的 head-only 分支内部已对 Y/Z 做镜像 (y=-y, z=-z)，
  // 这里必须用与画面相反的翻转策略，否则会出现双重镜像、动作反了
  const pasteMirror = !mirror
  if (pasteMirror) { cctx.translate(dx + ww, dy); cctx.scale(-1, 1); cctx.drawImage(av, 0, 0, ww, bh) }
  else { cctx.translate(dx, dy); cctx.drawImage(av, 0, 0, ww, bh) }   // ★ 必须 translate，否则永远画在 (0,0)
  cctx.restore()
}

// 背景虚化控件
function blurLabels() {
  if ($('blurv_px')) $('blurv_px').textContent = parseInt($('blur_px').value, 10)
}
on('blur_px', 'input', () => { blurLabels(); compositeRefresh() })
on('blur_invert', 'change', () => { compositeRefresh() })
on('blur_on', 'change', async (e) => {
  blurLabels()
  if (e.target.checked) {
    setStatus('加载背景分割模型…')
    await ensureSegmenter()
    if ($('blur_px') && parseFloat($('blur_px').value) < 2) $('blur_px').value = 14
    blurLabels()
  } else {
    hasMask = false
    setStatus('背景虚化已关闭')
  }
  compositeRefresh()
})

function compositeRefresh() {           // 没有实时源时，拖动滑块也能即时看到效果
  if (lastComp) {
    drawComposite(lastComp.srcEl, lastComp.lms, lastComp.w, lastComp.h)
    drawOutput(); drawSelectionOverlay()
  }
}
for (const id of ['cp_on','cp_size','cp_dx','cp_dy']) {
  const e = $(id); if (!e) continue
  e.addEventListener('input',  () => { cpLabels(); compositeRefresh() })
  e.addEventListener('change', () => { cpLabels(); compositeRefresh() })
}
if ($('view_reset')) $('view_reset').addEventListener('click', () => {
  const cam = avatar?.getRenderer()?.getCamera()
  if (cam) {
    cam.position.set(0, 0, 1.5)
    cam.fov = 40
    cam.updateProjectionMatrix()
    cam.lookAt(0, 0, 0)
  }
  applyTransform(); modelDiag()
  setStatus('已重置相机视图与模型变换')
})
if ($('cp_reset')) $('cp_reset').addEventListener('click', () => {
  $('cp_size').value = 1.8; $('cp_dx').value = 0; $('cp_dy').value = 0
  cpLabels(); compositeRefresh(); setStatus('已重置合成参数')
})

const T = ['t_scale','t_x','t_y','t_z']
// 抵消 aniface 写入模型根节点的平移（人脸矩阵的位置分量），
// 否则模型会在画布里跑偏，出现"只剩半张脸"。旋转保持不变。
function stabilizeModel() {
  const inner = avatar?.getRenderer()?.getAvatar()?.getScene()
  if (inner) {
    // 直接清零模型根矩阵的平移分量（只保留旋转/缩放）。
    // 不能用 wrapper.position 去抵消：人脸矩阵的平移量级与模型空间不一致，会把模型推到相机跟前。
    const e = inner.matrix.elements
    e[12] = 0; e[13] = 0; e[14] = 0
  }
  if (!wrapper) return
  const g = (id) => parseFloat($(id).value)
  // aniface 的 head-only 分支会把矩阵缩放 40 倍（isFullBodyAvatar()?1:40），
  // 若不对冲，模型会大 40 倍 —— 只有把 Scale 调到 ~0.025 才看得见。
  // 这里读内层实际缩放并抵消，使 Scale=1.0 恒等于"自然大小"。
  let innerScale = 1
  if (inner) {
    const p = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3()
    inner.matrix.decompose(p, q, s)
    if (s.x > 1e-6) innerScale = s.x
  }
  wrapper.scale.setScalar(g('t_scale') / innerScale)
  wrapper.position.set(g('t_x'), g('t_y'), g('t_z'))
}

// 模型侧诊断：看清到底是"模型被放大"还是"相机被拉近"
function modelDiag() {
  const el = $('mv_dbg'); if (!el) return
  const rnd = avatar?.getRenderer(); if (!rnd) { el.textContent = '模型未加载'; return }
  const inner = rnd.getAvatar()?.getScene()
  const cam = rnd.getCamera()
  let mScale = '-'
  if (inner) {
    const p = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3()
    inner.matrix.decompose(p, q, s)
    mScale = s.x.toFixed(3)
  }
  const c = cam ? cam.position : null
  el.textContent = `wrapper=${wrapper ? '有' : '无(位置滑块无效)'} · 模型内层缩放${mScale} · 设置缩放${parseFloat($('t_scale').value).toFixed(2)}`
    + (c ? ` · 相机(${c.x.toFixed(2)},${c.y.toFixed(2)},${c.z.toFixed(2)}) fov${cam.fov}` : '')
}

// 一步到位：更新 morph + 矩阵 -> 清平移 -> 渲染。
// 必须在 render 之前清平移，否则当前帧仍是被推偏的画面。
function stepAvatar(r) {
  const rnd = avatar?.getRenderer()
  if (!rnd) return
  if (r?.faceLandmarks?.length) { rnd.processLandmarks(r); stabilizeModel() }
  rnd.render()
  if ((cpTick++ % 20) === 0) modelDiag()
}

function applyTransform() {
  if (!wrapper) return
  const g = (id) => parseFloat($(id).value)
  const s = g('t_scale')
  $('tv_scale').textContent = s.toFixed(2)
  $('tv_x').textContent = g('t_x').toFixed(2)
  $('tv_y').textContent = g('t_y').toFixed(2)
  $('tv_z').textContent = g('t_z').toFixed(2)
  wrapper.scale.setScalar(s)
  stabilizeModel()
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
  const yawEl = $(SP.yaw)
  if (yawEl) {
    const yaw = parseFloat(yawEl.value)
    if ($('v_yaw')) $('v_yaw').textContent = yaw.toFixed(2)
    const sc = a.getScene()
    if (sc) { sc.matrixAutoUpdate = true; sc.rotation.y = yaw * 0.6; sc.updateMatrix() }
  }
  avatar.getRenderer().render()
}
for (const id of Object.values(SP)) on(id, 'input', onSlider)

// 启动时刷新一次标签
cpLabels()
blurLabels()

























// ---------------- 滚轮调节滑块 ----------------
// 悬停在 range 上滚动即可改值；步长默认取范围的 1%（避免 step 太小滚不动）
// Shift = 10 倍（粗调）  Alt = 1/10（微调）
document.addEventListener('wheel', (e) => {
  const el = e.target
  if (!el || el.tagName !== 'INPUT' || el.type !== 'range' || el.disabled) return
  const min = parseFloat(el.min), max = parseFloat(el.max)
  const step = parseFloat(el.step) || 1
  if (!isFinite(min) || !isFinite(max)) return
  let inc = Math.max(step, (max - min) / 100)
  if (e.shiftKey) inc *= 10
  else if (e.altKey) inc /= 10
  const dir = e.deltaY < 0 ? 1 : -1
  let v = parseFloat(el.value) + dir * inc
  v = Math.min(max, Math.max(min, v))
  // 对齐到 step 网格，避免出现 0.30000000000000004 之类的值
  v = Math.round(v / step) * step
  const decimals = (String(step).split('.')[1] || '').length
  v = parseFloat(v.toFixed(Math.min(decimals, 6)))
  if (v === parseFloat(el.value)) return
  e.preventDefault()                       // 阻止页面跟着滚
  el.value = v
  el.dispatchEvent(new Event('input', { bubbles: true }))
}, { passive: false })

// 给所有滑块加提示
document.querySelectorAll('input[type=range]').forEach((el) => {
  el.title = '滚轮可调 · Shift 粗调 · Alt 微调'
  el.style.cursor = 'ns-resize'
})

