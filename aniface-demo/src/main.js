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
    onReady: () => { setStatus('模型就绪 ✅'); ensureWrapper(); patchLiveFace(); applyTransform() },
    onError: (e) => setStatus('模型错误: ' + e.message)
  })
  await avatar.initialize()
  ensureWrapper()
  patchLiveFace()
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
      if (r?.faceLandmarks?.length) avatar.processLandmarkData(r)
      updateLiveCanvas(video, r?.faceLandmarks?.[0])
      fitOverlay(); drawOverlay(r); updateStats(r)
      drawComposite(video, r?.faceLandmarks?.[0], video.videoWidth, video.videoHeight)
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
      if (r?.faceLandmarks?.length) avatar.processLandmarkData(r)
      updateLiveCanvas(video, r?.faceLandmarks?.[0])
      fitOverlay(); drawOverlay(r); updateStats(r)
      drawComposite(video, r?.faceLandmarks?.[0], video.videoWidth, video.videoHeight)
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
    octx.drawImage(el, 0, 0, overlay.width, overlay.height)   // 图片画进摄像头面板
    updateLiveCanvas(el, r?.faceLandmarks?.[0])
    drawOverlay(r, true); updateStats(r)
    if (r?.faceLandmarks?.length) {
      avatar.processLandmarkData(r)
      drawComposite(el, r.faceLandmarks[0], el.naturalWidth || el.width, el.naturalHeight || el.height)
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

function cpLabels() {
  if (!$('cp_size')) return
  $('cpv_size').textContent = parseFloat($('cp_size').value).toFixed(2)
  $('cpv_dx').textContent   = parseFloat($('cp_dx').value).toFixed(2)
  $('cpv_dy').textContent   = parseFloat($('cp_dy').value).toFixed(2)
}

function drawComposite(srcEl, landmarks, srcW, srcH) {
  if (!comp || !cctx || !srcW || !srcH) return
  if (comp.width !== srcW || comp.height !== srcH) { comp.width = srcW; comp.height = srcH }
  const mirror = $('c_mirror') ? $('c_mirror').checked : true
  cctx.setTransform(1, 0, 0, 1, 0, 0)
  cctx.clearRect(0, 0, comp.width, comp.height)

  // ① 底层：原始画面
  cctx.save()
  if (mirror) { cctx.translate(comp.width, 0); cctx.scale(-1, 1) }
  cctx.drawImage(srcEl, 0, 0, comp.width, comp.height)
  cctx.restore()

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
  const cx = ((bx0 + bx1) / 2) * comp.width  + parseFloat($('cp_dx').value) * comp.width
  const cy = ((by0 + by1) / 2) * comp.height + parseFloat($('cp_dy').value) * comp.height

  // ③ 顶层：模型画布（透明背景）；按高度贴合，宽度等比
  const av = canvas
  const ww = bh * (av.width / av.height)
  const dx = cx - ww / 2, dy = cy - bh / 2
  cctx.save()
  cctx.imageSmoothingEnabled = true
  if (mirror) { cctx.translate(dx + ww, dy); cctx.scale(-1, 1); cctx.drawImage(av, 0, 0, ww, bh) }
  else cctx.drawImage(av, 0, 0, ww, bh)
  cctx.restore()
}

function compositeRefresh() {           // 没有实时源时，拖动滑块也能即时看到效果
  if (lastComp) drawComposite(lastComp.srcEl, lastComp.lms, lastComp.w, lastComp.h)
}
for (const id of ['cp_on','cp_size','cp_dx','cp_dy']) {
  const e = $(id); if (!e) continue
  e.addEventListener('input',  () => { cpLabels(); compositeRefresh() })
  e.addEventListener('change', () => { cpLabels(); compositeRefresh() })
}
if ($('cp_reset')) $('cp_reset').addEventListener('click', () => {
  $('cp_size').value = 1.8; $('cp_dx').value = 0; $('cp_dy').value = 0
  cpLabels(); compositeRefresh(); setStatus('已重置合成参数')
})

// ---------------- 摄像头贴脸（运行时着色器投影，无需改 GLB） ----------------
const LF = {
  canvas: document.createElement('canvas'),
  tex: null, uniforms: null, ready: false,
  // 脸部在投影 UV 中的目标矩形，默认值来自 Blender 端的投影参数
  box: { u0: 0.30, u1: 0.70, v0: 0.28, v1: 0.62 },
}
LF.canvas.width = LF.canvas.height = 512
const lfCtx = LF.canvas.getContext('2d')

function ensureLiveTexture() {
  if (LF.tex) return LF.tex
  const t = new THREE.CanvasTexture(LF.canvas)
  t.colorSpace = THREE.SRGBColorSpace
  t.flipY = true
  t.minFilter = THREE.LinearFilter
  t.magFilter = THREE.LinearFilter
  t.generateMipmaps = false
  LF.tex = t
  return t
}

// 把头部材质的片元着色器打补丁：按局部坐标算平面投影 UV，用画布的 alpha 做遮罩混入
function patchLiveFace() {
  if (LF.ready) return
  const scene = avatar?.getRenderer()?.getScene()
  if (!scene) return
  let head = null
  scene.traverse(o => { if (!head && o.isMesh && o.morphTargetDictionary) head = o })
  if (!head) return
  const geo = head.geometry
  if (!geo.boundingBox) geo.computeBoundingBox()
  const bb = geo.boundingBox
  // 与 Blender 端一致：u 覆盖 x，v 覆盖 y（模型 up），范围 U0..U1 / V0..V1
  const U0 = 0.20, U1 = 0.82, V0 = 0.19, V1 = 0.86
  const bu = (U1 - U0) / (bb.max.x - bb.min.x), au = U0 - bu * bb.min.x
  const bv = (V1 - V0) / (bb.max.y - bb.min.y), av = V0 - bv * bb.min.y
  const uni = {
    uLive:    { value: 0 },
    uLiveMap: { value: ensureLiveTexture() },
    uProj:    { value: new THREE.Vector4(au, bu, av, bv) },
  }
  LF.uniforms = uni
  const patch = (mat) => {
    mat.onBeforeCompile = (shader) => {
      // 保险：结构不匹配就跳过，避免整个材质编译失败
      if (!shader.vertexShader.includes('#include <begin_vertex>') ||
          !shader.fragmentShader.includes('#include <map_fragment>')) {
        console.warn('[liveface] 着色器结构不匹配，跳过注入')
        return
      }
      Object.assign(shader.uniforms, uni)
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nuniform vec4 uProj;\nvarying vec2 vLiveUV;\nvarying vec3 vLiveN;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\n  vLiveUV = vec2(uProj.x + uProj.y*transformed.x, uProj.z + uProj.w*transformed.y);\n  vLiveN = normal;')
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform float uLive;\nuniform sampler2D uLiveMap;\nvarying vec2 vLiveUV;\nvarying vec3 vLiveN;')
        .replace('#include <map_fragment>', [
          '#include <map_fragment>',
          'if (uLive > 0.001) {',
          '  float front = smoothstep(0.05, 0.45, vLiveN.z);',
          '  vec4 live = texture2D(uLiveMap, clamp(vLiveUV, 0.0, 1.0));',
          '  diffuseColor.rgb = mix(diffuseColor.rgb, live.rgb, uLive * front * live.a);',
          '}',
        ].join('\n'))
    }
    mat.needsUpdate = true
  }
  if (Array.isArray(head.material)) head.material.forEach(patch); else patch(head.material)
  LF.ready = true
  console.log('[liveface] patched on mesh:', head.name)
}

// 每帧把源画面（视频/图片）按人脸框对齐后画进画布；用 alpha 羽化边缘
function updateLiveCanvas(srcEl, landmarks) {
  const W = LF.canvas.width, H = LF.canvas.height
  if (!$('lf_on') || !$('lf_on').checked) {   // 面板不存在或未开启：不做逐帧上传，只清一次
    if (!LF._cleared) { lfCtx.clearRect(0, 0, W, H); if (LF.tex) LF.tex.needsUpdate = true; LF._cleared = true }
    return
  }
  LF._cleared = false
  lfCtx.setTransform(1, 0, 0, 1, 0, 0)
  lfCtx.globalCompositeOperation = 'source-over'
  lfCtx.clearRect(0, 0, W, H)
  if (LF.tex) LF.tex.needsUpdate = true
  if (!srcEl || !landmarks || !landmarks.length) return

  let x0 = 1, y0 = 1, x1 = 0, y1 = 0
  for (const p of landmarks) {
    if (p.x < x0) x0 = p.x; if (p.x > x1) x1 = p.x
    if (p.y < y0) y0 = p.y; if (p.y > y1) y1 = p.y
  }
  const fw = x1 - x0, fh = y1 - y0
  x0 -= fw * 0.10; x1 += fw * 0.10
  // 目标矩形对应「下巴 ~ 额头上方」，眼位约落在矩形 53% 高度处（与模型眼睛的 UV 位置吻合）
  y0 -= fh * 0.28; y1 += fh * 0.08

  const zoom = parseFloat($('lf_zoom').value), dxo = parseFloat($('lf_dx').value), dyo = parseFloat($('lf_dy').value)
  let u0 = LF.box.u0, u1 = LF.box.u1, v0 = LF.box.v0, v1 = LF.box.v1
  const cu = (u0 + u1) / 2 + dxo, cv = (v0 + v1) / 2 + dyo
  u0 = cu - (cu - u0) * zoom; u1 = cu + (u1 - cu) * zoom
  v0 = cv - (cv - v0) * zoom; v1 = cv + (v1 - cv) * zoom

  const dx = u0 * W, dy = (1 - v1) * H
  const dw = (u1 - u0) * W, dh = (v1 - v0) * H
  const sw = srcEl.videoWidth || srcEl.naturalWidth || srcEl.width
  const sh = srcEl.videoHeight || srcEl.naturalHeight || srcEl.height
  const sx = x0 * sw, sy = y0 * sh, sw2 = (x1 - x0) * sw, sh2 = (y1 - y0) * sh

  lfCtx.save()
  lfCtx.imageSmoothingEnabled = true
  if ($('c_mirror').checked) {
    lfCtx.translate(dx + dw, dy); lfCtx.scale(-1, 1)
    lfCtx.drawImage(srcEl, sx, sy, sw2, sh2, 0, 0, dw, dh)
  } else {
    lfCtx.drawImage(srcEl, sx, sy, sw2, sh2, dx, dy, dw, dh)
  }
  lfCtx.restore()

  // 边缘羽化：用径向渐变把矩形边缘的 alpha 压下去
  lfCtx.globalCompositeOperation = 'destination-in'
  const cx = dx + dw / 2, cy = dy + dh / 2
  const g = lfCtx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(dw, dh) * 0.62)
  g.addColorStop(0.72, 'rgba(0,0,0,1)')
  g.addColorStop(1.00, 'rgba(0,0,0,0)')
  lfCtx.fillStyle = g
  lfCtx.fillRect(dx, dy, dw, dh)
  lfCtx.globalCompositeOperation = 'source-over'
  if (LF.tex) LF.tex.needsUpdate = true
}

function applyLiveMix() {
  if (!LF.uniforms || !$('lf_on')) return
  const isOn = $('lf_on').checked
  const mix = parseFloat($('lf_mix').value)
  $('lfv_mix').textContent = mix.toFixed(2)
  $('lfv_zoom').textContent = parseFloat($('lf_zoom').value).toFixed(2)
  $('lfv_dx').textContent = parseFloat($('lf_dx').value).toFixed(2)
  $('lfv_dy').textContent = parseFloat($('lf_dy').value).toFixed(2)
  LF.uniforms.uLive.value = isOn ? mix : 0
  avatar?.getRenderer()?.render()
}
for (const id of ['lf_on','lf_mix','lf_zoom','lf_dx','lf_dy']) {
  const e = $(id); if (!e) continue
  e.addEventListener('input', applyLiveMix)
  e.addEventListener('change', applyLiveMix)
}
if ($('lf_reset')) $('lf_reset').addEventListener('click', () => {
  $('lf_zoom').value = 1; $('lf_dx').value = 0; $('lf_dy').value = 0; $('lf_mix').value = 0.85
  applyLiveMix(); setStatus('已重置贴脸对齐')
})

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

// 启动时刷新一次合成参数标签
cpLabels()


