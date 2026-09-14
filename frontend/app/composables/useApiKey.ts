const STORAGE_KEY = 'cases_api_key'

// login único, compartilhado pela equipe — chave fica salva no navegador,
// não pede de novo até o usuário sair ou a chave ser rejeitada pela API.
export function useApiKey() {
  const apiKey = useState<string | null>('apiKey', () => {
    if (import.meta.client) return localStorage.getItem(STORAGE_KEY)
    return null
  })

  function setApiKey(value: string) {
    apiKey.value = value
    if (import.meta.client) localStorage.setItem(STORAGE_KEY, value)
  }

  function clearApiKey() {
    apiKey.value = null
    if (import.meta.client) localStorage.removeItem(STORAGE_KEY)
  }

  return { apiKey, setApiKey, clearApiKey }
}
