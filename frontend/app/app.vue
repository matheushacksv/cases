<script setup lang="ts">
interface SegmentOut {
  id: number
  name: string
  n_cases: number
}
interface CaseOut {
  id: number
  name: string
  niche_raw: string
  result: string
  segment_id: number | null
  segment_name: string | null
}

const { apiBase } = useRuntimeConfig().public

const colorMode = useColorMode()
const isDark = computed({
  get: () => colorMode.value === 'dark',
  set: (v) => (colorMode.preference = v ? 'dark' : 'light'),
})

const q = ref('')
const debouncedQ = ref('')
let timer: ReturnType<typeof setTimeout> | undefined
watch(q, (v) => {
  clearTimeout(timer)
  timer = setTimeout(() => (debouncedQ.value = v), 300)
})

const segmentId = ref<number | null>(null)
// digitar busca desmarca o filtro de segmento
watch(debouncedQ, (v) => {
  if (v.trim()) segmentId.value = null
})

const PAGE_SIZE = 12
const page = ref(1)
// trocar busca/segmento volta pra página 1
watch([debouncedQ, segmentId], () => (page.value = 1))

const req = computed(() => buildRequest(debouncedQ.value, segmentId.value))

const { data: segments } = await useFetch<SegmentOut[]>('/segments', {
  baseURL: apiBase,
  default: () => [],
})

// muitos nichos viram parede de chips → mostra top N (mais volumosos), resto atrás de "ver mais"
const SEG_TOP = 8
const showAllSegments = ref(false)
const visibleSegments = computed(() => {
  if (showAllSegments.value) return segments.value
  const top = segments.value.slice(0, SEG_TOP)
  // nicho selecionado fora do top continua visível (senão filtro ativo "some")
  if (segmentId.value && !top.some((s) => s.id === segmentId.value)) {
    const sel = segments.value.find((s) => s.id === segmentId.value)
    if (sel) top.push(sel)
  }
  return top
})

interface Paged {
  items: CaseOut[]
  count: number
}

const { data, status, error } = await useFetch(() => req.value.path, {
  baseURL: apiBase,
  query: computed(() => ({
    ...req.value.params,
    // só /cases é paginado; /search é top-N
    ...(req.value.path === '/cases' ? { page: page.value } : {}),
  })),
  default: (): Paged => ({ items: [], count: 0 }),
  // /search devolve array, /cases devolve {items,count}. Normaliza pros dois.
  transform: (r: CaseOut[] | Paged): Paged =>
    Array.isArray(r) ? { items: r, count: r.length } : r,
})

const cases = computed(() => data.value.items)
const total = computed(() => data.value.count)

function selectSegment(id: number | null) {
  q.value = ''
  debouncedQ.value = ''
  segmentId.value = id
}
</script>

<template>
  <UApp>
    <UContainer class="max-w-4xl py-8">
      <header class="mb-6 flex items-start justify-between gap-2">
        <div>
          <h1 class="text-2xl font-bold">Cases</h1>
          <p class="text-muted">Consulta rápida de resultados por nicho</p>
        </div>
        <UButton
          :icon="isDark ? 'i-lucide-moon' : 'i-lucide-sun'"
          color="neutral"
          variant="ghost"
          size="lg"
          aria-label="Alternar tema"
          @click="isDark = !isDark"
        />
      </header>

      <UInput
        v-model="q"
        size="xl"
        icon="i-lucide-search"
        placeholder="buscar nicho ou resultado…"
        class="mb-4 w-full"
      />

      <div class="mb-6 flex flex-wrap gap-2">
        <UButton
          :color="segmentId === null ? 'primary' : 'neutral'"
          :variant="segmentId === null ? 'solid' : 'soft'"
          size="sm"
          @click="selectSegment(null)"
        >
          Todos
        </UButton>
        <UButton
          v-for="s in visibleSegments"
          :key="s.id"
          :color="segmentId === s.id ? 'primary' : 'neutral'"
          :variant="segmentId === s.id ? 'solid' : 'soft'"
          size="sm"
          @click="selectSegment(s.id)"
        >
          {{ s.name }}
          <UBadge color="neutral" variant="subtle" size="sm">{{ s.n_cases }}</UBadge>
        </UButton>
        <UButton
          v-if="segments.length > SEG_TOP"
          color="neutral"
          variant="ghost"
          size="sm"
          @click="showAllSegments = !showAllSegments"
        >
          {{ showAllSegments ? 'ver menos' : `+ mais ${segments.length - SEG_TOP} nichos` }}
        </UButton>
      </div>

      <div v-if="status === 'pending'" class="grid gap-4 sm:grid-cols-2">
        <USkeleton v-for="n in 4" :key="n" class="h-32" />
      </div>
      <UAlert
        v-else-if="error"
        color="error"
        title="Erro ao carregar cases"
        :description="String(error)"
      />
      <p v-else-if="!cases.length" class="py-12 text-center text-muted">
        Nenhum case encontrado.
      </p>
      <div v-else class="grid gap-4 sm:grid-cols-2">
        <CaseCard v-for="c in cases" :key="c.id" :case-item="c" />
      </div>

      <div v-if="total > PAGE_SIZE" class="mt-6 flex justify-center">
        <UPagination
          v-model:page="page"
          :total="total"
          :items-per-page="PAGE_SIZE"
        />
      </div>
    </UContainer>
  </UApp>
</template>
