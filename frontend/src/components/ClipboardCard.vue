<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'

const props = defineProps({
  content: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['delete'])

const copied = ref(false)

// 自定义渲染器
const renderer = new marked.Renderer()

renderer.code = function(code, language) {
  const lang = language || ''
  let highlighted
  if (lang && hljs.getLanguage(lang)) {
    highlighted = hljs.highlight(code, { language: lang }).value
  } else {
    highlighted = hljs.highlightAuto(code).value
  }
  const langLabel = lang || 'code'
  return `<div class="code-wrapper"><div class="code-header"><span class="code-lang">${langLabel}</span><button class="copy-code-btn" data-code="${encodeURIComponent(code)}">复制</button></div><pre><code class="hljs">${highlighted}</code></pre></div>`
}

marked.setOptions({
  renderer,
  breaks: true,
  gfm: true
})

// 判断是否为代码块或 Markdown
const isCodeOrMarkdown = computed(() => {
  const content = props.content.trim()
  // 代码块
  if (content.startsWith('```') || content.startsWith('`')) return true
  // Markdown 特殊语法
  if (/^(#{1,6}|\*|-|\+|\d+\.|>|---|\*\*|__|\[.*\]\(.*\)|!\[.*\]\(.*\))/m.test(content)) return true
  return false
})

// 渲染后的 HTML
const renderedContent = computed(() => {
  if (!isCodeOrMarkdown.value) return null
  try {
    return marked.parse(props.content)
  } catch {
    return null
  }
})

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

const copyCode = async (e) => {
  const btn = e.target.closest('.copy-code-btn')
  if (!btn) return
  const code = decodeURIComponent(btn.dataset.code)
  await navigator.clipboard.writeText(code)
  btn.textContent = '已复制'
  setTimeout(() => btn.textContent = '复制', 1500)
}
</script>

<template>
  <div class="bg-white dark:bg-[#1E1E1E] rounded-xl shadow-sm hover:shadow-md transition-all duration-200 p-4 group/card">
    <div class="flex items-start gap-3">
      <!-- 内容 -->
      <div class="flex-1 min-w-0">
        <!-- Markdown/代码渲染 -->
        <div
          v-if="renderedContent"
          class="prose prose-sm dark:prose-invert max-w-none text-[#191919] dark:text-[#E5E5E5] leading-relaxed markdown-body"
          v-html="renderedContent"
          @click="copyCode"
        ></div>
        <!-- 普通文本 -->
        <p v-else class="text-[#191919] dark:text-[#E5E5E5] break-all leading-relaxed whitespace-pre-wrap">
          {{ content }}
        </p>
      </div>

      <!-- 操作按钮 - 手机端始终显示，桌面端hover显示 -->
      <div class="flex items-center gap-2 opacity-100 md:opacity-0 md:group-hover/card:opacity-100 transition-opacity shrink-0">
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

<style>
.markdown-body {
  font-size: 14px;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body h1 { font-size: 1.5em; }
.markdown-body h2 { font-size: 1.3em; }
.markdown-body h3 { font-size: 1.15em; }

.markdown-body p {
  margin: 0.5em 0;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.markdown-body li {
  margin: 0.25em 0;
}

.markdown-body blockquote {
  border-left: 3px solid #07C160;
  padding-left: 1em;
  margin: 0.5em 0;
  color: #888888;
}

.markdown-body a {
  color: #07C160;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body strong {
  font-weight: 600;
}

.markdown-body em {
  font-style: italic;
}

.markdown-body code:not(pre code) {
  background: #F5F5F5;
  padding: 0.15em 0.4em;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
}

.dark .markdown-body code:not(pre code) {
  background: #2A2A2A;
}

/* 代码块样式 */
.code-wrapper {
  margin: 0.75em 0;
  border-radius: 8px;
  overflow: hidden;
  background: #282c34;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #21252b;
  border-bottom: 1px solid #333;
}

.code-lang {
  font-size: 12px;
  color: #888;
  text-transform: uppercase;
}

.copy-code-btn {
  padding: 2px 8px;
  font-size: 12px;
  color: #888;
  background: transparent;
  border: 1px solid #444;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-code-btn:hover {
  color: #fff;
  border-color: #07C160;
  background: rgba(7, 193, 96, 0.2);
}

.markdown-body pre {
  margin: 0;
  background: #282c34;
  padding: 1em;
  overflow-x: auto;
}

.markdown-body pre code {
  font-family: 'Consolas', 'Monaco', 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.5;
  background: transparent;
  padding: 0;
}
</style>