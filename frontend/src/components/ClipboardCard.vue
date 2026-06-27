<script setup>
import { computed, h, nextTick, ref } from 'vue'
import { NButton, NIcon, NInput, NSpace, NTooltip, createDiscreteApi } from 'naive-ui'
import {
  CheckmarkOutline,
  CopyOutline,
  CreateOutline,
  TrashOutline,
} from '@vicons/ionicons5'

const props = defineProps({
  id: {
    type: Number,
    required: true,
  },
  content: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['delete', 'update'])
const { message, dialog } = createDiscreteApi(['message', 'dialog'])
const copied = ref(false)
const editing = ref(false)
const draftContent = ref('')
const editInputRef = ref(null)

const renderIcon = (icon) => () => h(NIcon, null, { default: () => h(icon) })
const blockPreview = computed(() => props.content.trim() || '空内容')

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.content)
    copied.value = true
    message.success('已复制到剪贴板')
    setTimeout(() => {
      copied.value = false
    }, 1600)
  } catch (err) {
    message.error('复制失败，当前浏览器可能要求 HTTPS')
    console.error('复制失败:', err)
  }
}

const startEdit = async () => {
  draftContent.value = props.content
  editing.value = true
  await nextTick()
  editInputRef.value?.focus?.()
}

const cancelEdit = () => {
  editing.value = false
  draftContent.value = ''
}

const saveEdit = () => {
  const nextContent = draftContent.value.trim()
  if (!nextContent) {
    message.warning('内容不能为空')
    return
  }

  if (nextContent === props.content) {
    cancelEdit()
    return
  }

  emit('update', { id: props.id, content: nextContent })
  editing.value = false
}

const handleEditKeydown = (e) => {
  if (e.key === 'Escape') {
    e.preventDefault()
    cancelEdit()
  }

  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    saveEdit()
  }
}

const confirmDelete = () => {
  dialog.warning({
    title: '删除这条内容？',
    content: '删除后会从所有已连接设备中移除。',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: () => emit('delete'),
  })
}
</script>

<template>
  <article class="notion-block" :class="{ 'is-editing': editing }">
    <div v-if="editing" class="block-editor">
      <n-input
        ref="editInputRef"
        v-model:value="draftContent"
        type="textarea"
        :autosize="{ minRows: 2, maxRows: 10 }"
        placeholder="修改文本"
        :input-props="{ id: `copyhub-edit-${props.id}`, name: `copyhub-edit-${props.id}` }"
        @keydown="handleEditKeydown"
      />
      <div class="block-editor__actions">
        <n-space justify="end">
          <n-button @click="cancelEdit">取消</n-button>
          <n-button type="primary" @click="saveEdit">保存</n-button>
        </n-space>
      </div>
    </div>

    <template v-else>
      <div class="block-content">
        <span class="block-handle" aria-hidden="true">⋮⋮</span>
        <p>{{ blockPreview }}</p>
      </div>

      <div class="block-actions">
        <n-tooltip trigger="hover">
          <template #trigger>
            <n-button
              quaternary
              circle
              size="small"
              :type="copied ? 'success' : 'default'"
              :render-icon="renderIcon(copied ? CheckmarkOutline : CopyOutline)"
              @click="copyToClipboard"
            />
          </template>
          {{ copied ? '已复制' : '复制内容' }}
        </n-tooltip>
        <n-tooltip trigger="hover">
          <template #trigger>
            <n-button quaternary circle size="small" :render-icon="renderIcon(CreateOutline)" @click="startEdit" />
          </template>
          修改
        </n-tooltip>
        <n-tooltip trigger="hover">
          <template #trigger>
            <n-button quaternary circle size="small" type="error" :render-icon="renderIcon(TrashOutline)" @click="confirmDelete" />
          </template>
          删除
        </n-tooltip>
      </div>
    </template>
  </article>
</template>
