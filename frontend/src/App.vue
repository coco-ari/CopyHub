<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import ClipboardCard from './components/ClipboardCard.vue'
import InputBox from './components/InputBox.vue'

const API_URL = '/api'
const WS_URL = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`

// WebSocket 连接
let ws = null
let reconnectTimer = null

const connectWebSocket = () => {
  ws = new WebSocket(WS_URL)

  ws.onopen = () => {
    console.log('WebSocket 已连接')
  }

  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data)
      handleWebSocketMessage(message)
    } catch (err) {
      // ping/pong 消息
    }
  }

  ws.onclose = () => {
    console.log('WebSocket 已断开，尝试重连...')
    reconnectTimer = setTimeout(connectWebSocket, 3000)
  }

  ws.onerror = () => {
    ws.close()
  }
}

const handleWebSocketMessage = (message) => {
  if (message.type === 'create') {
    // 新增消息，添加到列表末尾（最新消息在底部）
    const newItem = {
      ...message.data,
      createdAt: new Date(message.data.created_at)
    }
    clipboardItems.value.push(newItem)
    // 滚动到底部
    scrollToBottom()
  } else if (message.type === 'delete') {
    // 删除消息
    clipboardItems.value = clipboardItems.value.filter(item => item.id !== message.data.id)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: 'smooth'
    })
  })
}

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
  // 连接 WebSocket
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) ws.close()
  if (reconnectTimer) clearTimeout(reconnectTimer)
})

// 剪贴板数据
const clipboardItems = ref([])

// 获取数据
const fetchItems = async () => {
  try {
    const res = await fetch(`${API_URL}/items`)
    const data = await res.json()
    // 反转数组，最新消息显示在底部
    clipboardItems.value = data.reverse().map(item => ({
      ...item,
      createdAt: new Date(item.created_at)
    }))
    // 滚动到最新消息
    scrollToBottom()
  } catch (err) {
    console.error('获取数据失败:', err)
  }
}

// 添加新内容
const addContent = async (content) => {
  if (!content.trim()) return
  try {
    await fetch(`${API_URL}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: content.trim() })
    })
    // WebSocket 会推送更新，无需手动刷新
  } catch (err) {
    console.error('添加失败:', err)
  }
}

// 删除内容
const deleteItem = async (id) => {
  try {
    await fetch(`${API_URL}/items/${id}`, { method: 'DELETE' })
    // WebSocket 会推送更新，无需手动更新
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
    // 当前数据是旧->新顺序，比较当前消息与前一条（更旧的）消息的时间差
    const timeDiff = prevItem ? item.createdAt - prevItem.createdAt : Infinity

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
        <div class="flex items-center gap-3">
          <!-- GitHub 图标 -->
          <a
            href="https://github.com/coco-ari/CopyHub"
            target="_blank"
            :title="`⭐ Star on GitHub`"
            class="w-9 h-9 rounded-full bg-white dark:bg-[#2A2A2A] flex items-center justify-center hover:bg-[#F5F5F5] dark:hover:bg-[#3A3A3A] transition-colors"
          >
            <svg class="w-5 h-5 text-[#191919] dark:text-[#E5E5E5]" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
            </svg>
          </a>
          <h1 class="text-xl font-semibold text-[#191919] dark:text-[#E5E5E5] flex items-center gap-3">
            <!-- Logo 图标 - CH 透明背景 -->
            <span class="text-[#07C160] font-bold text-lg tracking-tight">
              CH
            </span>
            CopyHub
          </h1>
        </div>
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