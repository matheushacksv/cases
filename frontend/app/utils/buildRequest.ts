export interface ApiRequest {
  path: string
  params: Record<string, string | number>
}

// Decide qual endpoint chamar a partir do estado da tela.
// Prioridade: busca digitada > segmento selecionado > lista recente.
// has_video só existe em /cases — /search (semântico) não suporta esse filtro.
export function buildRequest(
  query: string,
  segmentId: number | null,
  hasVideo: boolean,
): ApiRequest {
  if (query.trim()) return { path: '/search', params: { query } }
  const params: Record<string, string | number> = {}
  if (segmentId) params.segment_id = segmentId
  if (hasVideo) params.has_video = 'true'
  return { path: '/cases', params }
}
