<script setup lang="ts">
import type { CaseOut } from '~/types'

defineProps<{ caseItem: CaseOut; downloadUrl: string }>()
defineEmits<{ edit: []; copy: [] }>()
</script>

<template>
  <div class="flex gap-1">
    <UButton
      v-if="caseItem.video_url"
      :to="caseItem.video_url"
      target="_blank"
      rel="noopener noreferrer"
      icon="i-lucide-video"
      color="primary"
      variant="ghost"
      size="sm"
      aria-label="Abrir vídeo de feedback"
    />
    <UButton
      v-if="caseItem.video_url"
      :to="downloadUrl"
      icon="i-lucide-download"
      color="neutral"
      variant="ghost"
      size="sm"
      aria-label="Baixar vídeo em mp4 (pra mandar no WhatsApp como vídeo, não documento)"
    />
    <UButton
      icon="i-lucide-pencil"
      color="neutral"
      variant="ghost"
      size="sm"
      aria-label="Editar case"
      @click="$emit('edit')"
    />
    <UButton
      icon="i-lucide-copy"
      color="neutral"
      variant="ghost"
      size="sm"
      aria-label="Copiar resultado"
      @click="$emit('copy')"
    />
  </div>
</template>
