<script setup>
import { ref, nextTick } from 'vue'

const emit = defineEmits(['submit'])

const inputText = ref('')
const textareaRef = ref(null)

const submit = () => {
  if (!inputText.value.trim()) return
  emit('submit', inputText.value)
  inputText.value = ''
  // 重置高度
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
    }
  })
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  }
}

const autoResize = () => {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 150) + 'px'
}
</script>

<template>
  <div class="fixed bottom-0 left-0 right-0 p-3 bg-[#EDEDED] dark:bg-[#111111] border-t border-[#E5E5E5] dark:border-[#2A2A2A]">
    <div class="max-w-2xl mx-auto">
      <div class="flex items-end gap-3">
        <textarea
          ref="textareaRef"
          v-model="inputText"
          placeholder="输入文字... (Shift+Enter 换行)"
          rows="1"
          class="flex-1 bg-white dark:bg-[#2A2A2A] rounded-lg px-4 py-3 text-[#191919] dark:text-[#E5E5E5] placeholder:text-[#888888] outline-none border-none resize-none"
          @keydown="handleKeydown"
          @input="autoResize"
        ></textarea>
        <button
          @click="submit"
          :disabled="!inputText.trim()"
          class="px-6 py-3 rounded-lg bg-[#07C160] hover:bg-[#1AAD19] disabled:bg-[#CCCCCC] dark:disabled:bg-[#3A3A3A] disabled:cursor-not-allowed text-white font-medium transition-colors shrink-0"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>