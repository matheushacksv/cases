<script setup lang="ts">
import type { CaseOut } from '~/types'

const props = defineProps<{ caseItem: CaseOut }>()
const emit = defineEmits<{ edit: [CaseOut] }>()

const LIMIT = 220
const expanded = ref(false)
const isLong = computed(() => props.caseItem.result.length > LIMIT)
const shown = computed(() =>
  expanded.value || !isLong.value
    ? props.caseItem.result
    : props.caseItem.result.slice(0, LIMIT) + '…',
)

const toast = useToast()
async function copy() {
  await navigator.clipboard.writeText(props.caseItem.result)
  toast.add({ title: 'Resultado copiado', color: 'success', icon: 'i-lucide-check' })
}
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <h3 class="font-semibold break-words">{{ caseItem.name }}</h3>
          <div class="mt-1 flex items-center gap-2">
            <UBadge v-if="caseItem.segment_name" color="primary" variant="subtle" size="sm">
              {{ caseItem.segment_name }}
            </UBadge>
            <span
              v-if="caseItem.niche_raw !== caseItem.segment_name"
              class="text-xs text-muted truncate"
            >
              {{ caseItem.niche_raw }}
            </span>
          </div>
        </div>
        <div class="flex gap-1">
          <UButton
            icon="i-lucide-pencil"
            color="neutral"
            variant="ghost"
            size="sm"
            aria-label="Editar case"
            @click="emit('edit', caseItem)"
          />
          <UButton
            icon="i-lucide-copy"
            color="neutral"
            variant="ghost"
            size="sm"
            aria-label="Copiar resultado"
            @click="copy"
          />
        </div>
      </div>
    </template>

    <p class="whitespace-pre-line text-sm">{{ shown }}</p>
    <UButton
      v-if="isLong"
      variant="link"
      color="primary"
      size="sm"
      class="px-0 mt-1"
      @click="expanded = !expanded"
    >
      {{ expanded ? 'ver menos' : 'ver mais' }}
    </UButton>
  </UCard>
</template>
