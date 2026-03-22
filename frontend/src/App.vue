<script setup>
import { ref, computed, onMounted } from 'vue'
import ClipboardCard from './components/ClipboardCard.vue'
import InputBox from './components/InputBox.vue'

const API_URL = '/api'

// 主题切换
const isDark = ref(false)

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

// 初始化主题
onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
  // 加载数据
  fetchItems()
})

// 剪贴板数据
const clipboardItems = ref([])

// 获取数据
const fetchItems = async () => {
  try {
    const res = await fetch(`${API_URL}/items`)
    const data = await res.json()
    clipboardItems.value = data.map(item => ({
      ...item,
      createdAt: new Date(item.created_at)
    }))
  } catch (err) {
    console.error('获取数据失败:', err)
  }
}

// 添加新内容
const addContent = async (content) => {
  if (!content.trim()) return
  try {
    const res = await fetch(`${API_URL}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: content.trim() })
    })
    if (res.ok) {
      await fetchItems()
    }
  } catch (err) {
    console.error('添加失败:', err)
  }
}

// 删除内容
const deleteItem = async (id) => {
  try {
    const res = await fetch(`${API_URL}/items/${id}`, { method: 'DELETE' })
    if (res.ok) {
      clipboardItems.value = clipboardItems.value.filter(item => item.id !== id)
    }
  } catch (err) {
    console.error('删除失败:', err)
  }
}

// 时间分组（5分钟阈值）
const groupedItems = computed(() => {
  const groups = []
  const threshold = 5 * 60 * 1000 // 5分钟

  clipboardItems.value.forEach((item, index) => {
    const prevItem = clipboardItems.value[index - 1]
    const timeDiff = prevItem ? prevItem.createdAt - item.createdAt : Infinity

    if (timeDiff > threshold) {
      groups.push({
        isTimeSeparator: true,
        time: item.createdAt,
        id: `time-${item.id}`
      })
    }
    groups.push({
      ...item,
      isTimeSeparator: false
    })
  })

  return groups
})
</script>

<template>
  <div class="min-h-screen bg-[#EDEDED] dark:bg-[#111111] transition-colors duration-300">
    <!-- 头部 -->
    <header class="sticky top-0 z-10 bg-[#EDEDED] dark:bg-[#111111] border-b border-[#E5E5E5] dark:border-[#2A2A2A]">
      <div class="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
        <h1 class="text-xl font-semibold text-[#191919] dark:text-[#E5E5E5] flex items-center gap-3">
          <!-- Logo 图标 - CH 透明背景 -->
          <span class="text-[#07C160] font-bold text-lg tracking-tight">
            CH
          </span>
          CopyHub
        </h1>
        <button
          @click="toggleTheme"
          class="w-10 h-10 rounded-full bg-white dark:bg-[#2A2A2A] flex items-center justify-center hover:bg-gray-100 dark:hover:bg-[#3A3A3A] transition-colors"
          :title="isDark ? '切换到浅色模式' : '切换到深色模式'"
        >
          <!-- 太阳图标 (深色模式显示) -->
          <svg v-if="isDark" class="w-5 h-5 text-[#E5E5E5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="5" stroke-width="2"/>
            <path stroke-width="2" stroke-linecap="round" d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
          </svg>
          <!-- 月亮图标 (浅色模式显示) -->
          <svg v-else class="w-5 h-5 text-[#191919]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
          </svg>
        </button>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="max-w-2xl mx-auto px-4 py-4 pb-32">
      <div class="space-y-3">
        <template v-for="item in groupedItems" :key="item.id">
          <!-- 时间分隔 -->
          <div v-if="item.isTimeSeparator" class="text-center py-3">
            <span class="text-xs text-[#888888] bg-[#D8D8D8] dark:bg-[#2A2A2A] px-3 py-1 rounded-sm">
              {{ $formatTime(item.time) }}
            </span>
          </div>
          <!-- 剪贴板卡片 -->
          <ClipboardCard
            v-else
            :content="item.content"
            @delete="deleteItem(item.id)"
          />
        </template>
      </div>
    </main>

    <!-- 底部输入框 -->
    <InputBox @submit="addContent" />
  </div>
</template>