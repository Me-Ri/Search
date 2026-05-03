<template>
  <div class="h-screen overflow-hidden text-gray-900 font-sans bg-[url('/1.jpg')] bg-cover bg-center bg-no-repeat">
    <div class="h-full overflow-y-auto bg-white/15 backdrop-blur-[2px]" style="scrollbar-width: none; -ms-overflow-style: none;">
      <div class="max-w-6xl mx-auto px-16 py-10">

        <!-- Header -->
        <div class="mb-8">
          <h1 class="text-2xl font-semibold tracking-tight">Проверка документов</h1>
          <p class="text-base text-gray-500 mt-1">
            Загрузите шаблон и документы для проверки структуры, содержания и форматирования
          </p>
        </div>

        <!-- Upload zones -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
          <!-- Шаблон — одиночный файл -->
          <DropZone
            label="Шаблон (эталон)"
            icon="📄"
            :file="files.template"
            @file-selected="files.template = $event"
            @file-removed="files.template = null"
          />

          <!-- Документы — множественная загрузка -->
          <MultiDropZone
            label="Документы для проверки"
            icon="📋"
            :files="files.documents"
            @files-added="onDocumentsAdded"
            @file-removed="removeDocument"
          />
        </div>

        <!-- Controls -->
        <div class="flex flex-wrap items-center gap-3 mb-5">
          <div class="flex items-center gap-2">
            <label class="text-base text-gray-500">Модель:</label>
            <select
              v-model="model"
              class="text-base border border-gray-200 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option>gpt-oss:120b</option>
            </select>
          </div>
          <button
            :disabled="!canRun || loading"
            @click="runCheck"
            class="px-5 py-2 text-base font-medium rounded-lg bg-blue-600 text-white transition-all
                  hover:bg-blue-700 active:scale-95
                  disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {{ loading ? 'Проверяем...' : 'Запустить проверку' }}
          </button>
        </div>

        <!-- Progress -->
        <div v-if="loading" class="mb-5">
          <div class="h-1 bg-gray-200 rounded-full overflow-hidden">
            <div
              class="h-full bg-blue-500 rounded-full transition-all duration-500"
              :style="{ width: overallProgress + '%' }"
            ></div>
          </div>
          <p class="text-lg text-gray-400 mt-1.5">{{ progressLabel }}</p>
        </div>

        <!-- Error alert -->
        <div
          v-if="globalError"
          class="mb-5 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-base text-red-700"
        >
          {{ globalError }}
        </div>

        <!-- Results per file -->
        <template v-if="fileResults.length">
          <hr class="border-gray-100 my-6" />
          <h2 class="text-base font-semibold mb-3">Результаты проверки</h2>

          <div class="flex flex-col gap-3">
            <div
              v-for="fr in fileResults"
              :key="fr.fileName"
              class="border border-gray-200 rounded-xl overflow-hidden bg-white"
            >
              <!-- File accordion header -->
              <button
                @click="fr.open = !fr.open"
                class="w-full flex items-center justify-between px-5 py-4 text-base font-medium bg-gray-50 hover:bg-gray-100 transition-colors text-left"
              >
                <span class="flex items-center gap-3">
                  <!-- Status icon -->
                  <span v-if="fr.loading" class="text-xl animate-spin">⏳</span>
                  <span v-else-if="fr.error" class="text-xl">❌</span>
                  <span v-else-if="fr.result && fr.result.errors?.length === 0" class="text-xl">✅</span>
                  <span v-else class="text-xl">⚠️</span>

                  <span class="text-gray-800 break-all">{{ fr.fileName }}</span>

                  <!-- Error count badge -->
                  <span
                    v-if="!fr.loading && !fr.error && fr.result"
                    class="text-xs font-normal rounded-full px-2 py-0.5"
                    :class="fr.result.errors?.length ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'"
                  >
                    {{ fr.result.errors?.length ? fr.result.errors.length + ' ошибок' : 'OK' }}
                  </span>

                  <span v-if="fr.loading" class="text-xs font-normal text-gray-400 bg-gray-200 rounded-full px-2 py-0.5">
                    Проверяется...
                  </span>
                </span>

                <span class="text-gray-400 text-lg flex-shrink-0 ml-2">{{ fr.open ? '▲' : '▼' }}</span>
              </button>

              <!-- File accordion body -->
              <div v-if="fr.open" class="p-5">
                <!-- Loading state -->
                <div v-if="fr.loading" class="text-base text-gray-400">
                  Идёт проверка файла...
                </div>

                <!-- Error state -->
                <div v-else-if="fr.error" class="px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-base text-red-700">
                  {{ fr.error }}
                </div>

                <!-- Result -->
                <template v-else-if="fr.result">
                  <!-- Metrics -->
                  <div class="grid grid-cols-3 gap-3 mb-5">
                    <div
                      v-for="m in getMetrics(fr.result)"
                      :key="m.label"
                      class="bg-gray-50 border border-gray-100 rounded-xl px-4 py-3"
                    >
                      <div class="text-lg text-gray-400 mb-1">{{ m.label }}</div>
                      <div class="text-2xl font-semibold text-gray-900">{{ m.value }}</div>
                    </div>
                  </div>

                  <!-- No errors -->
                  <div
                    v-if="!fr.result.errors?.length"
                    class="px-4 py-3 rounded-lg bg-green-50 border border-green-200 text-base text-green-700"
                  >
                    Ошибок не найдено — документ полностью соответствует шаблону.
                  </div>

                  <!-- Error groups -->
                  <div v-else class="flex flex-col gap-2">
                    <div v-for="(group, key) in fr.groupedErrors" :key="key">
                      <div v-if="group.errors.length" class="border border-gray-100 rounded-xl overflow-hidden">
                        <button
                          @click="group.open = !group.open"
                          class="w-full flex items-center justify-between px-4 py-3 text-base font-medium
                                bg-gray-50 hover:bg-gray-100 transition-colors text-left"
                        >
                          <span class="flex items-center gap-2">
                            {{ group.label }}
                            <span class="text-lg font-normal bg-gray-200 text-gray-600 rounded-full px-2 py-0.5">
                              {{ group.errors.length }}
                            </span>
                          </span>
                          <span class="text-gray-400 text-lg">{{ group.open ? '▲' : '▼' }}</span>
                        </button>

                        <div v-if="group.open" class="p-3 flex flex-col gap-2 bg-white">
                          <template v-for="sev in ['critical', 'high', 'medium', 'low']" :key="sev">
                            <template v-if="bySev(group.errors, sev).length">
                              <div class="text-lg font-semibold uppercase tracking-widest text-gray-400 mt-1">
                                {{ sevEmoji(sev) }} {{ sev }}
                              </div>
                              <div
                                v-for="err in bySev(group.errors, sev)"
                                :key="err.description"
                                class="rounded-lg border border-gray-100 border-l-4 px-3 py-2.5 bg-gray-50"
                                :class="sevBorderClass(sev)"
                              >
                                <div class="text-base font-medium text-gray-800">{{ err.section || 'Общий' }}</div>
                                <div class="text-lg text-gray-500 mt-0.5 leading-relaxed">{{ err.description }}</div>
                              </div>
                            </template>
                          </template>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Download -->
                  <button
                    @click="downloadReport(fr)"
                    class="mt-4 text-base px-4 py-2 rounded-lg border border-gray-200 bg-white
                          hover:bg-gray-50 transition-colors text-gray-700"
                  >
                    Скачать отчёт (JSON)
                  </button>
                </template>
              </div>
            </div>
          </div>
        </template>

        <!-- Hint -->
        <p v-if="!fileResults.length && !loading" class="text-base text-gray-400 mt-4">
          Загрузите шаблон и один или несколько документов для запуска проверки.
        </p>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, defineComponent, h } from 'vue'

// ── DropZone (single file, inline sub-component) ──────────────────────────────
const DropZone = defineComponent({
  name: 'DropZone',
  props: { label: String, icon: String, file: Object },
  emits: ['file-selected', 'file-removed'],
  setup(props, { emit }) {
    const dragOver = ref(false)
    const inputRef = ref(null)

    const onDrop = (e) => {
      dragOver.value = false
      const f = e.dataTransfer.files[0]
      if (f?.name.endsWith('.docx')) emit('file-selected', f)
    }
    const onFile = (e) => {
      const f = e.target.files[0]
      if (f) emit('file-selected', f)
    }
    const formatSize = (bytes) =>
      bytes < 1024 * 1024
        ? (bytes / 1024).toFixed(1) + ' КБ'
        : (bytes / 1024 / 1024).toFixed(1) + ' МБ'

    return () => {
      const base =
        'flex items-center justify-center rounded-xl border-2 border-dashed min-h-32 p-6 text-center cursor-pointer transition-all duration-150 '
      const state = dragOver.value
        ? 'border-blue-400 bg-blue-50'
        : props.file
        ? 'border-green-300 bg-green-50'
        : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'

      return h('div', {
        class: base + state,
        onDragover: (e) => { e.preventDefault(); dragOver.value = true },
        onDragleave: () => { dragOver.value = false },
        onDrop,
        onClick: () => inputRef.value?.click(),
      }, [
        h('input', { ref: inputRef, type: 'file', accept: '.docx', class: 'hidden', onChange: onFile }),
        props.file
          ? h('div', { class: 'flex flex-col items-center gap-1' }, [
              h('div', { class: 'text-2xl' }, '✅'),
              h('div', { class: 'text-base font-medium text-gray-800 break-all max-w-xs' }, props.file.name),
              h('div', { class: 'text-lg text-gray-400' }, formatSize(props.file.size)),
              h('button', {
                class: 'mt-2 text-lg px-3 py-1 rounded-md bg-red-50 border border-red-200 text-red-600 hover:bg-red-100 transition-colors',
                onClick: (e) => { e.stopPropagation(); emit('file-removed') },
              }, 'Удалить'),
            ])
          : h('div', { class: 'flex flex-col items-center gap-1' }, [
              h('div', { class: 'text-2xl' }, props.icon),
              h('div', { class: 'text-base font-medium text-gray-700 mt-1' }, props.label),
              h('div', { class: 'text-lg text-gray-400 mt-0.5' }, '.docx — перетащите или нажмите'),
            ]),
      ])
    }
  },
})

// ── MultiDropZone (multiple files, inline sub-component) ──────────────────────
const MultiDropZone = defineComponent({
  name: 'MultiDropZone',
  props: { label: String, icon: String, files: Array },
  emits: ['files-added', 'file-removed'],
  setup(props, { emit }) {
    const dragOver = ref(false)
    const inputRef = ref(null)

    const onDrop = (e) => {
      dragOver.value = false
      const newFiles = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.docx'))
      if (newFiles.length) emit('files-added', newFiles)
    }
    const onFile = (e) => {
      const newFiles = Array.from(e.target.files)
      if (newFiles.length) emit('files-added', newFiles)
      e.target.value = ''
    }
    const formatSize = (bytes) =>
      bytes < 1024 * 1024
        ? (bytes / 1024).toFixed(1) + ' КБ'
        : (bytes / 1024 / 1024).toFixed(1) + ' МБ'

    return () => {
      const hasFiles = props.files && props.files.length > 0
      const base = 'rounded-xl border-2 border-dashed transition-all duration-150 '
      const state = dragOver.value
        ? 'border-blue-400 bg-blue-50'
        : hasFiles
        ? 'border-green-300 bg-green-50'
        : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'

      const children = []

      // Drop area (always visible)
      children.push(
        h('div', {
          class: 'flex flex-col items-center justify-center min-h-24 p-4 text-center cursor-pointer',
          onClick: () => inputRef.value?.click(),
          onDragover: (e) => { e.preventDefault(); dragOver.value = true },
          onDragleave: () => { dragOver.value = false },
          onDrop,
        }, [
          h('input', { ref: inputRef, type: 'file', accept: '.docx', multiple: true, class: 'hidden', onChange: onFile }),
          h('div', { class: 'text-2xl' }, hasFiles ? '➕' : props.icon),
          h('div', { class: 'text-base font-medium text-gray-700 mt-1' }, hasFiles ? 'Добавить ещё файлы' : props.label),
          h('div', { class: 'text-lg text-gray-400 mt-0.5' }, '.docx — перетащите или нажмите'),
        ])
      )

      // File list
      if (hasFiles) {
        children.push(
          h('div', { class: 'border-t border-gray-200 px-4 pb-3 flex flex-col gap-2' },
            props.files.map((f, i) =>
              h('div', {
                key: f.name + i,
                class: 'flex items-center justify-between gap-2 pt-2',
              }, [
                h('div', { class: 'flex items-center gap-2 min-w-0' }, [
                  h('span', { class: 'text-base' }, '📋'),
                  h('div', { class: 'min-w-0' }, [
                    h('div', { class: 'text-base text-gray-800 truncate' }, f.name),
                    h('div', { class: 'text-lg text-gray-400' }, formatSize(f.size)),
                  ]),
                ]),
                h('button', {
                  class: 'flex-shrink-0 text-lg px-2.5 py-1 rounded-md bg-red-50 border border-red-200 text-red-600 hover:bg-red-100 transition-colors',
                  onClick: (e) => { e.stopPropagation(); emit('file-removed', i) },
                }, '✕'),
              ])
            )
          )
        )
      }

      return h('div', {
        class: base + state,
        onDragover: (e) => { e.preventDefault(); dragOver.value = true },
        onDragleave: () => { dragOver.value = false },
        onDrop,
      }, children)
    }
  },
})

// ── State ─────────────────────────────────────────────────────────────────────
const files         = reactive({ template: null, documents: [] })
const model         = ref('gpt-oss:120b')
const loading       = ref(false)
const progressLabel = ref('')
const globalError   = ref('')
const fileResults   = ref([])  // Array of { fileName, file, open, loading, error, result, groupedErrors }

// ── File management ───────────────────────────────────────────────────────────
function onDocumentsAdded(newFiles) {
  for (const f of newFiles) {
    // Avoid duplicates by name
    if (!files.documents.find(d => d.name === f.name)) {
      files.documents.push(f)
    }
  }
}

function removeDocument(index) {
  files.documents.splice(index, 1)
}

// ── Computed ──────────────────────────────────────────────────────────────────
const canRun = computed(() => files.template && files.documents.length > 0)

const overallProgress = computed(() => {
  if (!fileResults.value.length) return 0
  const done = fileResults.value.filter(fr => !fr.loading).length
  return Math.round((done / fileResults.value.length) * 100)
})

// ── Helpers ───────────────────────────────────────────────────────────────────
const sevEmoji = (s) => ({ critical: '🔴', high: '🟠', medium: '🟡', low: '🟢' }[s] ?? '⚪')
const bySev    = (errs, sev) => errs.filter(e => e.severity === sev)
const sevBorderClass = (sev) => ({
  critical: 'border-l-red-500',
  high:     'border-l-orange-400',
  medium:   'border-l-yellow-400',
  low:      'border-l-green-400',
}[sev] ?? 'border-l-gray-300')

function getMetrics(result) {
  const errs = result.errors ?? []
  return [
    { label: 'Ошибок всего',   value: errs.length },
    { label: 'Структурных',    value: errs.filter(e => e.error_type === 'structural').length },
    { label: 'Форматирования', value: errs.filter(e => e.error_type === 'formatting').length },
  ]
}

function buildGroupedErrors(errors) {
  return reactive({
    structural: { label: 'Структура',      errors: errors.filter(e => e.error_type === 'structural'), open: false },
    formatting: { label: 'Форматирование', errors: errors.filter(e => e.error_type === 'formatting'), open: false },
    content:    { label: 'Содержание',     errors: errors.filter(e => e.error_type === 'content'),    open: false },
    typography: { label: 'Типографика',    errors: errors.filter(e => e.error_type === 'typography'), open: false },
  })
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function runCheck() {
  loading.value     = true
  globalError.value = ''

  // Init result entries for all documents
  fileResults.value = files.documents.map(f => ({
    fileName:     f.name,
    file:         f,
    open:         false,
    loading:      true,
    error:        null,
    result:       null,
    groupedErrors: buildGroupedErrors([]),
  }))

  progressLabel.value = `Проверяем ${files.documents.length} документов...`

  // Run all checks concurrently
  await Promise.all(
    fileResults.value.map(fr => checkSingleFile(fr))
  )

  loading.value       = false
  progressLabel.value = 'Готово'
}

async function checkSingleFile(fr) {
  try {
    const fd = new FormData()
    fd.append('template_file', files.template)
    fd.append('document_file',  fr.file)
    fd.append('model',     model.value)

    const res = await fetch('http://localhost:8000/api/validate-upload', { method: 'POST', body: fd })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    if (data.error) throw new Error(data.error)

    fr.result        = data
    fr.groupedErrors = buildGroupedErrors(data.errors ?? [])
  } catch (e) {
    fr.error = 'Ошибка: ' + e.message
  } finally {
    fr.loading = false
  }
}

function downloadReport(fr) {
  if (!fr.result) return
  const report = {
    template:           files.template?.name,
    document:           fr.fileName,
    model:              model.value,
    result:             fr.result,
    timestamp:          new Date().toISOString(),
    checked_formatting: true,
  }
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const a = Object.assign(document.createElement('a'), {
    href:     URL.createObjectURL(blob),
    download: `report_${fr.fileName.replace('.docx', '')}_${Date.now()}.json`,
  })
  a.click()
  URL.revokeObjectURL(a.href)
}
</script>