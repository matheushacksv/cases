// Check da lógica não-trivial de seleção de endpoint.
// Roda com: node buildRequest.check.ts   (Node >= 23 / v24 faz type-stripping nativo)
import assert from 'node:assert/strict'
import { buildRequest } from './app/utils/buildRequest.ts'

// busca digitada tem prioridade sobre segmento
assert.deepEqual(buildRequest('dentista', 5), {
  path: '/search',
  params: { query: 'dentista' },
})

// só espaços não conta como busca → cai no segmento
assert.deepEqual(buildRequest('   ', 5), {
  path: '/cases',
  params: { segment_id: 5 },
})

// segmento selecionado, sem busca
assert.deepEqual(buildRequest('', 5), {
  path: '/cases',
  params: { segment_id: 5 },
})

// nada selecionado → lista recente
assert.deepEqual(buildRequest('', null), { path: '/cases', params: {} })

console.log('buildRequest OK')
