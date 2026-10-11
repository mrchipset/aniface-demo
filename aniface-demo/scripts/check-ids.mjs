// 自检：main.js 里所有 $('id') 是否都能在 index.html 找到
// 用法: npm run check
import fs from 'node:fs'

const js   = fs.readFileSync(new URL('../src/main.js', import.meta.url), 'utf8')
const html = fs.readFileSync(new URL('../index.html',  import.meta.url), 'utf8')

const jsIds   = [...new Set([...js.matchAll(/\$\('([A-Za-z0-9_]+)'\)/g)].map(m => m[1]))]
const htmlIds = new Set([...html.matchAll(/id="([A-Za-z0-9_]+)"/g)].map(m => m[1]))

const missing = jsIds.filter(id => !htmlIds.has(id))

if (missing.length === 0) {
  console.log(`✅ 全部 ${jsIds.length} 个 id 都能对上`)
  process.exit(0)
}

console.error('❌ main.js 引用了 index.html 中不存在的 id：')
for (const id of missing) {
  const lines = js.split('\n').map((l, i) => [i + 1, l]).filter(([, l]) => l.includes(`$('${id}')`))
  for (const [n, l] of lines) console.error(`   L${n}: ${l.trim()}`)
}
console.error('\n提示：若该元素是可选 UI，请把访问包在判空里（例如用 on() 助手或 if ($(id))）。')
process.exit(1)
