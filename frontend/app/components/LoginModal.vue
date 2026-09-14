<script setup lang="ts">
const open = defineModel<boolean>({ default: false })
const emit = defineEmits<{ success: [] }>()

const { setApiKey } = useApiKey()
const password = ref('')

function submit() {
  if (!password.value.trim()) return
  setApiKey(password.value.trim())
  password.value = ''
  open.value = false
  emit('success')
}
</script>

<template>
  <UModal v-model:open="open" title="Entrar" description="Senha compartilhada da equipe">
    <template #body>
      <form class="flex flex-col gap-4" @submit.prevent="submit">
        <UInput
          v-model="password"
          type="password"
          placeholder="Senha da equipe"
          autofocus
          size="lg"
        />
        <UButton type="submit" block :disabled="!password.trim()">Entrar</UButton>
      </form>
    </template>
  </UModal>
</template>
