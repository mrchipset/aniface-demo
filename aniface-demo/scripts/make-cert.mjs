import selfsigned from 'selfsigned'
import fs from 'node:fs'
import os from 'node:os'
import { X509Certificate } from 'node:crypto'

const ips = new Set(['127.0.0.1'])
for (const list of Object.values(os.networkInterfaces()))
  for (const i of list || []) if (i.family === 'IPv4' && !i.internal) ips.add(i.address)

const altNames = [
  { type: 2, value: 'localhost' },
  ...[...ips].map(ip => ({ type: 7, ip })),
]
console.log('SAN entries:', ['localhost', ...ips].join(', '))

const notBeforeDate = new Date()
const notAfterDate = new Date(notBeforeDate); notAfterDate.setFullYear(notAfterDate.getFullYear() + 2)

const pems = await selfsigned.generate(
  [{ name: 'commonName', value: 'aniface-demo' }],
  {
    keyType: 'rsa', keySize: 2048, algorithm: 'sha256',
    notBeforeDate, notAfterDate,
    extensions: [
      { name: 'basicConstraints', cA: false },
      { name: 'keyUsage', digitalSignature: true, keyEncipherment: true },
      { name: 'extKeyUsage', serverAuth: true },
      { name: 'subjectAltName', altNames },
    ],
  }
)
fs.mkdirSync('certs', { recursive: true })
fs.writeFileSync('certs/key.pem', pems.private)
fs.writeFileSync('certs/cert.pem', pems.cert)

const x = new X509Certificate(pems.cert)
console.log('CN      :', x.subject)
console.log('issuer  :', x.issuer)
console.log('valid   :', x.validFrom, '~', x.validTo)
console.log('SAN     :', x.subjectAltName)
console.log('wrote certs/key.pem + certs/cert.pem')
