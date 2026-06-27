<script setup>
import { computed, h, ref } from 'vue'
import { NButton, NIcon, NInput, NTooltip } from 'naive-ui'
import { SendOutline } from '@vicons/ionicons5'

const emit = defineEmits(['submit'])

const inputText = ref('')
const isSending = ref(false)

const canSubmit = computed(() => inputText.value.trim().length > 0 && !isSending.value)
const renderSendIcon = () => h(NIcon, null, { default: () => h(SendOutline) })

const submit = () => {
  if (!canSubmit.value) return
  isSending.value = true
  emit('submit', inputText.value)
  inputText.value = ''

  setTimeout(() => {
    isSending.value = false
  }, 180)
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  }
}
</script>

<template>
  <div class="composer-shell">
    <div class="notion-composer">
      <n-input
        v-model:value="inputText"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 6 }"
        placeholder="输入文字，Enter 发送"
        class="composer-input"
        :input-props="{ id: 'copyhub-composer', name: 'copyhub-composer' }"
        @keydown="handleKeydown"
      />
      <n-tooltip trigger="hover">
        <template #trigger>
          <n-button
            circle
            secondary
            type="primary"
            class="send-icon-button"
            :render-icon="renderSendIcon"
            :disabled="!canSubmit"
            :loading="isSending"
            aria-label="发送"
            @click="submit"
          />
        </template>
        发送
      </n-tooltip>
    </div>
  </div>
</template>
