export interface ApiRequest {
  path: string
  params: Record<string, string | number>
}

// Decide qual endpoint chamar a partir do estado da tela.
// Prioridade: busca digitada > segmento selecionado > lista recente.
export function buildRequest(query: string, segmentId: number | null): ApiRequest {
  if (query.trim()) return { path: '/search', params: { query } }
  if (segmentId) return { path: '/cases', params: { segment_id: segmentId } }
  return { path: '/cases', params: {} }
}
