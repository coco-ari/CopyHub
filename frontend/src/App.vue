<script setup>
import { computed, h, nextTick, onMounted, onUnmounted, ref } from 'vue'
import {
  NButton,
  NConfigProvider,
  NEmpty,
  NIcon,
  NMessageProvider,
  NTag,
  NTooltip,
  createDiscreteApi,
  darkTheme,
} from 'naive-ui'
import {
  ChatbubbleEllipsesOutline,
  CheckmarkCircleOutline,
  MoonOutline,
  RefreshOutline,
  SunnyOutline,
  WarningOutline,
  WifiOutline,
} from '@vicons/ionicons5'
import ClipboardCard from './components/ClipboardCard.vue'
import InputBox from './components/InputBox.vue'

const API_URL = '/api'
const ITEMS_PAGE_SIZE = 100
const HEARTBEAT_INTERVAL_MS = 15000
const HEARTBEAT_TIMEOUT_MS = 45000
const WS_URL = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`
const { message } = createDiscreteApi(['message'])

let ws = null
let heartbeatTimer = null
let lastSocketActivityAt = 0
let shouldReconnect = true

const isDark = ref(false)
const clipboardItems = ref([])
const loading = ref(false)
const errorMessage = ref('')
const connectionState = ref('connecting')

const naiveTheme = computed(() => (isDark.value ? darkTheme : null))
const themeOverrides = {
  common: {
    primaryColor: '#2f6f4e',
    primaryColorHover: '#285f43',
    primaryColorPressed: '#224f39',
    borderRadius: '6px',
    fontWeightStrong: '650',
  },
}

const connectionMeta = computed(() => {
  const map = {
    connected: {
      label: '实时同步中',
      type: 'success',
      icon: CheckmarkCircleOutline,
    },
    connecting: {
      label: '正在连接',
      type: 'warning',
      icon: WifiOutline,
    },
    reconnecting: {
      label: '正在重连',
      type: 'warning',
      icon: WifiOutline,
    },
    disconnected: {
      label: '连接已断开',
      type: 'error',
      icon: WarningOutline,
    },
  }
  return map[connectionState.value] || map.connecting
})

const isRefreshWorking = computed(() => (
  loading.value ||
  connectionState.value === 'connecting' ||
  connectionState.value === 'reconnecting'
))

const refreshButtonClass = computed(() => ({
  'refresh-status-button': true,
  'is-ws-connected': connectionState.value === 'connected' && !loading.value,
  'is-ws-disconnected': connectionState.value === 'disconnected',
  'is-ws-reconnecting': isRefreshWorking.value,
}))

const refreshTooltip = computed(() => {
  if (connectionState.value === 'disconnected') {
    return 'WebSocket 已断开，点击刷新内容并重连'
  }
  if (connectionState.value === 'connected') {
    return loading.value ? '正在刷新内容' : 'WebSocket 连接正常，点击刷新内容'
  }
  return '正在刷新内容并重连'
})

const renderIcon = (icon) => () => h(NIcon, null, { default: () => h(icon) })

const clearHeartbeatTimer = () => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

const markWebSocketDisconnected = () => {
  if (!shouldReconnect) return
  clearHeartbeatTimer()
  connectionState.value = 'disconnected'
}

const startHeartbeat = (socket) => {
  clearHeartbeatTimer()
  lastSocketActivityAt = Date.now()

  heartbeatTimer = setInterval(() => {
    if (ws !== socket) return
    if (socket.readyState !== WebSocket.OPEN) {
      markWebSocketDisconnected()
      return
    }

    if (Date.now() - lastSocketActivityAt > HEARTBEAT_TIMEOUT_MS) {
      markWebSocketDisconnected()
      socket.close()
      return
    }

    socket.send('ping')
  }, HEARTBEAT_INTERVAL_MS)
}

const connectWebSocket = (options = {}) => {
  const { state = 'connecting' } = options
  clearHeartbeatTimer()

  if (ws) {
    ws.onopen = null
    ws.onmessage = null
    ws.onclose = null
    ws.onerror = null
    ws.close()
  }

  connectionState.value = state
  const socket = new WebSocket(WS_URL)
  ws = socket

  socket.onopen = () => {
    if (ws !== socket) return
    connectionState.value = 'connected'
    startHeartbeat(socket)
    fetchItems({ silent: true })
  }

  socket.onmessage = (event) => {
    if (ws !== socket) return
    lastSocketActivityAt = Date.now()
    if (event.data === 'pong') return

    try {
      const socketMessage = JSON.parse(event.data)
      handleWebSocketMessage(socketMessage)
    } catch (err) {
      // Non-JSON messages are heartbeat responses.
    }
  }

  socket.onclose = () => {
    if (ws !== socket) return
    markWebSocketDisconnected()
  }

  socket.onerror = () => {
    if (ws !== socket) return
    markWebSocketDisconnected()
    socket.close()
  }
}

const handleWebSocketMessage = (socketMessage) => {
  if (socketMessage.type === 'create') {
    const newItem = normalizeItem(socketMessage.data)
    const exists = clipboardItems.value.some(item => item.id === newItem.id)
    if (!exists) {
      clipboardItems.value.push(newItem)
      scrollToBottom()
    }
  } else if (socketMessage.type === 'update') {
    const updatedItem = normalizeItem(socketMessage.data)
    const index = clipboardItems.value.findIndex(item => item.id === updatedItem.id)
    if (index !== -1) {
      clipboardItems.value[index] = updatedItem
    }
  } else if (socketMessage.type === 'delete') {
    clipboardItems.value = clipboardItems.value.filter(item => item.id !== socketMessage.data.id)
  }
}

const normalizeItem = (item) => ({
  ...item,
  createdAt: new Date(item.created_at),
})

const getResponseError = async (res) => {
  const body = await res.json().catch(() => ({}))
  return new Error(body.detail || `HTTP ${res.status}`)
}

const scrollToBottom = () => {
  nextTick(() => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth',
    })
  })
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const initializeTheme = () => {
  const savedTheme = localStorage.getItem('theme')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  isDark.value = savedTheme === 'dark' || (!savedTheme && prefersDark)
  document.documentElement.classList.toggle('dark', isDark.value)
}

const fetchItems = async (options = {}) => {
  const { silent = false } = options
  if (!silent) loading.value = true
  errorMessage.value = ''

  try {
    const res = await fetch(`${API_URL}/items?limit=${ITEMS_PAGE_SIZE}&offset=0`)
    if (!res.ok) throw await getResponseError(res)
    const data = await res.json()
    clipboardItems.value = data.reverse().map(normalizeItem)
    scrollToBottom()
  } catch (err) {
    errorMessage.value = '无法加载剪贴板内容，请检查后端服务。'
    if (!silent) message.error(errorMessage.value)
    console.error('获取数据失败:', err)
  } finally {
    loading.value = false
  }
}

const handleRefreshClick = async () => {
  if (isRefreshWorking.value) return

  const needsReconnect = connectionState.value !== 'connected' || ws?.readyState !== WebSocket.OPEN
  if (needsReconnect) {
    connectionState.value = 'reconnecting'
  }

  await fetchItems()

  if (needsReconnect && shouldReconnect) {
    connectWebSocket({ state: 'reconnecting' })
  }
}

const addContent = async (content) => {
  if (!content.trim()) return

  try {
    const res = await fetch(`${API_URL}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: content.trim() }),
    })
    if (!res.ok) throw await getResponseError(res)

    const savedItem = normalizeItem(await res.json())
    const exists = clipboardItems.value.some(item => item.id === savedItem.id)
    if (!exists) {
      clipboardItems.value.push(savedItem)
      scrollToBottom()
    }
  } catch (err) {
    message.error(err.message || '发送失败，请稍后重试')
    console.error('添加失败:', err)
  }
}

const updateItem = async ({ id, content }) => {
  if (!content.trim()) return

  try {
    const res = await fetch(`${API_URL}/items/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: content.trim() }),
    })
    if (!res.ok) throw await getResponseError(res)

    const updatedItem = normalizeItem(await res.json())
    const index = clipboardItems.value.findIndex(item => item.id === updatedItem.id)
    if (index !== -1) {
      clipboardItems.value[index] = updatedItem
    }
    message.success('已修改')
  } catch (err) {
    message.error(err.message || '修改失败，请稍后重试')
    console.error('修改失败:', err)
  }
}

const deleteItem = async (id) => {
  try {
    const res = await fetch(`${API_URL}/items/${id}`, { method: 'DELETE' })
    if (!res.ok) throw await getResponseError(res)
    clipboardItems.value = clipboardItems.value.filter(item => item.id !== id)
    message.success('已删除')
  } catch (err) {
    message.error('删除失败，请稍后重试')
    console.error('删除失败:', err)
  }
}

const groupedItems = computed(() => {
  const groups = []
  const threshold = 5 * 60 * 1000

  clipboardItems.value.forEach((item, index) => {
    const prevItem = clipboardItems.value[index - 1]
    const timeDiff = prevItem ? item.createdAt - prevItem.createdAt : Infinity

    if (timeDiff > threshold) {
      groups.push({
        isTimeSeparator: true,
        time: item.createdAt,
        id: `time-${item.id}`,
      })
    }
    groups.push({
      ...item,
      isTimeSeparator: false,
    })
  })

  return groups
})

onMounted(() => {
  initializeTheme()
  fetchItems()
  connectWebSocket()
})

onUnmounted(() => {
  shouldReconnect = false
  if (ws) ws.close()
  clearHeartbeatTimer()
})
</script>

<template>
  <n-config-provider :theme="naiveTheme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <div class="notion-shell">
        <header class="notion-topbar">
          <div class="notion-topbar__inner">
            <div class="brand-block">
              <div class="brand-mark">CH</div>
              <div>
                <h1>CopyHub</h1>
                <p>Shared clipboard</p>
              </div>
            </div>

            <div class="topbar-actions">
              <n-tag
                class="connection-tag"
                :type="connectionMeta.type"
                round
                :bordered="false"
              >
                <template #icon>
                  <n-icon><component :is="connectionMeta.icon" /></n-icon>
                </template>
                {{ connectionMeta.label }}
              </n-tag>
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-button
                    circle
                    secondary
                    :class="refreshButtonClass"
                    :render-icon="renderIcon(RefreshOutline)"
                    :aria-label="refreshTooltip"
                    @click="handleRefreshClick"
                  />
                </template>
                {{ refreshTooltip }}
              </n-tooltip>
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-button
                    circle
                    secondary
                    :render-icon="renderIcon(isDark ? SunnyOutline : MoonOutline)"
                    @click="toggleTheme"
                  />
                </template>
                {{ isDark ? '切换到浅色模式' : '切换到深色模式' }}
              </n-tooltip>
            </div>
          </div>
        </header>

        <main class="notion-page">
          <section class="page-title">
            <div class="page-icon">
              <n-icon><ChatbubbleEllipsesOutline /></n-icon>
            </div>
            <h2>Clipboard</h2>
          </section>

          <div v-if="errorMessage" class="inline-alert">
            {{ errorMessage }}
          </div>

          <section class="document-stream" :class="{ 'is-loading': loading }">
            <n-empty
              v-if="!loading && groupedItems.length === 0"
              description="还没有剪贴板内容"
            />

            <div v-else class="block-list">
              <template v-for="item in groupedItems" :key="item.id">
                <div v-if="item.isTimeSeparator" class="time-separator">
                  <span>{{ $formatTime(item.time) }}</span>
                </div>
                <ClipboardCard
                  v-else
                  :id="item.id"
                  :content="item.content"
                  @delete="deleteItem(item.id)"
                  @update="updateItem"
                />
              </template>
            </div>
          </section>
        </main>

        <InputBox @submit="addContent" />
      </div>
    </n-message-provider>
  </n-config-provider>
</template>
