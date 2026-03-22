<script setup>
import { ref } from 'vue'

const props = defineProps({
  content: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['delete'])

const copied = ref(false)

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.content)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 1500)
  } catch (err) {
    console.error('复制失败:', err)
  }
}
</script>

<template>
  <div class="bg-white dark:bg-[#1E1E1E] rounded-xl shadow-sm hover:shadow-md transition-all duration-200 p-4 group/card">
    <div class="flex items-start gap-3">
      <!-- 内容 -->
      <p class="flex-1 text-[#191919] dark:text-[#E5E5E5] break-all leading-relaxed">
        {{ content }}
      </p>

      <!-- 操作按钮 - 手机端始终显示，桌面端hover显示 -->
      <div class="flex items-center gap-2 opacity-100 md:opacity-0 md:group-hover/card:opacity-100 transition-opacity">
        <!-- 复制按钮 -->
        <button
          @click="copyToClipboard"
          class="w-8 h-8 rounded-full bg-[#F5F5F5] dark:bg-[#2A2A2A] flex items-center justify-center hover:bg-[#07C160] dark:hover:bg-[#07C160] transition-colors group/btn"
          :title="copied ? '已复制' : '复制'"
        >
          <!-- 已复制图标 -->
          <svg v-if="copied" class="w-4 h-4 text-[#07C160]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <!-- 复制图标 -->
          <svg v-else class="w-4 h-4 text-[#888888] group-hover/btn:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <rect x="9" y="9" width="13" height="13" rx="2" stroke-width="2"/>
            <path stroke-width="2" d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
          </svg>
        </button>

        <!-- 删除按钮 -->
        <button
          @click="emit('delete')"
          class="w-8 h-8 rounded-full bg-[#F5F5F5] dark:bg-[#2A2A2A] flex items-center justify-center hover:bg-red-500 transition-colors group/btn"
          title="删除"
        >
          <svg class="w-4 h-4 text-[#888888] group-hover/btn:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>