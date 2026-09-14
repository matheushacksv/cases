<script setup lang="ts">
import type { CaseOut } from '~/types'

const open = defineModel<boolean>({ default: false })
const props = defineProps<{ caseItem?: CaseOut | null }>()
const emit = defineEmits<{ saved: []; unauthorized: [] }>()

const { apiBase } = useRuntimeConfig().public
const { apiKey, clearApiKey } = useApiKey()
const toast = useToast()

const isEdit = computed(() => !!props.caseItem)
const name = ref('')
const niche = ref('')
const result = ref('')
const loading = ref(false)

// preenche o form quando o modal abre (create limpa, edit carrega o case)
watch(open, (v) => {
  if (!v) return
  name.value = props.caseItem?.name ?? ''
  niche.value = props.caseItem?.niche_raw ?? ''
  result.value = props.caseItem?.result ?? ''
})

const valid = computed(() => name.value.trim() && niche.value.trim() && result.value.trim())

async function submit() {
  if (!valid.value || !apiKey.value) return
  loading.value = true
  try {
    if (isEdit.value) {
      await $fetch(`/cases/${props.caseItem!.id}`, {
        baseURL: apiBase,
        method: 'PATCH',
        headers: { 'X-API-Key': apiKey.value },
        body: { name: name.value, niche: niche.value, result: result.value },
      })
    } else {
      await $fetch('/cases', {
        baseURL: apiBase,
        method: 'POST',
        headers: { 'X-API-Key': apiKey.value },
        body: { name: name.value, niche_raw: niche.value, result: result.value },
      })
    }
    toast.add({ title: 'Case salvo', color: 'success', icon: 'i-lucide-check' })
    emit('saved')
  } catch (e: unknown) {
    const err = e as { status?: number; statusCode?: number; response?: { status?: number } }
    const status = err?.status ?? err?.statusCode ?? err?.response?.status
    if (status === 401) {
      clearApiKey()
      open.value = false
      emit('unauthorized')
      toast.add({ title: 'Senha inválida', color: 'error', icon: 'i-lucide-x' })
    } else if (status === 503) {
      toast.add({ title: 'Classificação indisponível, tenta de novo', color: 'error' })
    } else {
      toast.add({ title: 'Erro ao salvar case', color: 'error' })
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    :title="isEdit ? 'Editar case' : 'Novo case'"
  >
    <template #body>
      <form class="flex flex-col gap-4" @submit.prevent="submit">
        <UInput v-model="name" placeholder="Nome" size="lg" maxlength="150" />
        <UInput v-model="niche" placeholder="Nicho" size="lg" maxlength="150" />
        <UTextarea v-model="result" placeholder="Resultado" :rows="5" />
        <UButton type="submit" block :loading="loading" :disabled="!valid">
          Salvar
        </UButton>
      </form>
    </template>
  </UModal>
</template>
