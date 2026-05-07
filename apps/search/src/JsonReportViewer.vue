<template>
  <div class="h-screen overflow-hidden text-gray-900 font-sans bg-[url('/1.jpg')] bg-cover bg-center bg-no-repeat">
    <div class="h-full overflow-y-auto bg-white/15 backdrop-blur-[2px]" style="scrollbar-width: none; -ms-overflow-style: none;">
      <div class="max-w-6xl mx-auto px-16 py-10">

        <!-- Header -->
        <div class="mb-8">
          <h1 class="text-2xl font-semibold tracking-tight">Просмотр отчёта</h1>
          <p class="text-base text-gray-500 mt-1">
            Загрузите JSON-отчёт для просмотра результатов проверки
          </p>
        </div>

        <!-- Upload zone -->
        <div
          class="rounded-xl border-2 border-dashed transition-all duration-150 min-h-36 flex items-center justify-center text-center cursor-pointer mb-6"
          :class="dragOver
            ? 'border-blue-400 bg-blue-50'
            : reportLoaded
            ? 'border-green-300 bg-green-50'
            : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'"
          @click="inputRef.click()"
          @dragover.prevent="dragOver = true"
          @dragleave="dragOver = false"
          @drop.prevent="onDrop"
        >
          <input
            ref="inputRef"
            type="file"
            accept=".json"
            class="hidden"
            @change="onFileInput"
          />

          <div v-if="!reportLoaded" class="flex flex-col items-center gap-1 py-6 px-4">
            <div class="text-3xl">📂</div>
            <div class="text-base font-medium text-gray-700 mt-1">Загрузить JSON-отчёт</div>
            <div class="text-sm text-gray-400 mt-0.5">.json — перетащите или нажмите</div>
          </div>

          <div v-else class="flex flex-col items-center gap-1 py-6 px-4">
            <div class="text-3xl">✅</div>
            <div class="text-base font-medium text-gray-800 break-all max-w-xs">{{ loadedFileName }}</div>
            <button
              class="mt-2 text-sm px-3 py-1 rounded-md bg-red-50 border border-red-200 text-red-600 hover:bg-red-100 transition-colors"
              @click.stop="clearReport"
            >
              Удалить
            </button>
          </div>
        </div>

        <!-- Parse error -->
        <div
          v-if="parseError"
          class="mb-5 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-base text-red-700"
        >
          {{ parseError }}
        </div>

        <!-- Report content -->
        <template v-if="report">

          <!-- Meta info -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
            <div class="bg-white border border-gray-100 rounded-xl px-4 py-3">
              <div class="text-sm text-gray-400 mb-1">Документ</div>
              <div class="text-base font-medium text-gray-800 break-all">{{ report.document ?? '—' }}</div>
            </div>
            <div class="bg-white border border-gray-100 rounded-xl px-4 py-3">
              <div class="text-sm text-gray-400 mb-1">Шаблон</div>
              <div class="text-base font-medium text-gray-800 break-all">{{ report.template ?? '—' }}</div>
            </div>
            <div class="bg-white border border-gray-100 rounded-xl px-4 py-3">
              <div class="text-sm text-gray-400 mb-1">Модель</div>
              <div class="text-base font-medium text-gray-800">{{ report.model ?? '—' }}</div>
            </div>
            <div class="bg-white border border-gray-100 rounded-xl px-4 py-3">
              <div class="text-sm text-gray-400 mb-1">Дата проверки</div>
              <div class="text-base font-medium text-gray-800">{{ formattedDate }}</div>
            </div>
          </div>

          <!-- Result block -->
          <div class="border border-gray-200 rounded-xl overflow-hidden bg-white">

            <!-- Header -->
            <div class="flex items-center justify-between px-5 py-4 bg-gray-50">
              <span class="flex items-center gap-3">
                <span v-if="errors.length === 0" class="text-xl">✅</span>
                <span v-else class="text-xl">⚠️</span>
                <span class="text-base font-medium text-gray-800 break-all">{{ report.document }}</span>
                <span
                  class="text-xs font-normal rounded-full px-2 py-0.5"
                  :class="errors.length ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'"
                >
                  {{ errors.length ? errors.length + ' ошибок' : 'OK' }}
                </span>
              </span>
            </div>

            <!-- Body -->
            <div class="p-5">

              <!-- Metrics -->
              <div class="grid grid-cols-3 gap-3 mb-5">
                <div
                  v-for="m in metrics"
                  :key="m.label"
                  class="bg-gray-50 border border-gray-100 rounded-xl px-4 py-3"
                >
                  <div class="text-sm text-gray-400 mb-1">{{ m.label }}</div>
                  <div class="text-2xl font-semibold text-gray-900">{{ m.value }}</div>
                </div>
              </div>

              <!-- No errors -->
              <div
                v-if="errors.length === 0"
                class="px-4 py-3 rounded-lg bg-green-50 border border-green-200 text-base text-green-700"
              >
                Ошибок не найдено — документ полностью соответствует шаблону.
              </div>

              <!-- Error groups -->
              <div v-else class="flex flex-col gap-2">
                <div v-for="(group, key) in groupedErrors" :key="key">
                  <div v-if="group.errors.length" class="border border-gray-100 rounded-xl overflow-hidden">
                    <button
                      @click="group.open = !group.open"
                      class="w-full flex items-center justify-between px-4 py-3 text-base font-medium
                             bg-gray-50 hover:bg-gray-100 transition-colors text-left"
                    >
                      <span class="flex items-center gap-2">
                        {{ group.label }}
                        <span class="text-sm font-normal bg-gray-200 text-gray-600 rounded-full px-2 py-0.5">
                          {{ group.errors.length }}
                        </span>
                      </span>
                      <span class="text-gray-400 text-lg">{{ group.open ? '▲' : '▼' }}</span>
                    </button>

                    <div v-if="group.open" class="p-3 flex flex-col gap-2 bg-white">
                      <template v-for="sev in ['critical', 'high', 'medium', 'low']" :key="sev">
                        <template v-if="bySev(group.errors, sev).length">
                          <div class="text-xs font-semibold uppercase tracking-widest text-gray-400 mt-1">
                            {{ sevEmoji(sev) }} {{ sev }}
                          </div>
                          <div
                            v-for="err in bySev(group.errors, sev)"
                            :key="err.description"
                            class="rounded-lg border border-gray-100 border-l-4 px-3 py-2.5 bg-gray-50"
                            :class="sevBorderClass(sev)"
                          >
                            <div class="text-base font-medium text-gray-800">{{ err.section || 'Общий' }}</div>
                            <div class="text-sm text-gray-500 mt-0.5 leading-relaxed">{{ err.description }}</div>
                          </div>
                        </template>
                      </template>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>

        </template>

        <!-- Hint -->
        <p v-if="!report && !parseError" class="text-base text-gray-400 mt-4">
          Загрузите JSON-файл отчёта, скачанный после проверки документов.
        </p>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

// ── Refs ───────────────────────────────────────────────────────────────────────
const inputRef     = ref(null)
const dragOver     = ref(false)
const parseError   = ref('')
const report       = ref(null)
const loadedFileName = ref('')

// ── Derived ────────────────────────────────────────────────────────────────────
const reportLoaded = computed(() => !!report.value)

const errors = computed(() => report.value?.result?.errors ?? [])

const metrics = computed(() => {
  const errs = errors.value
  return [
    { label: 'Ошибок всего',   value: errs.length },
    { label: 'Структурных',    value: errs.filter(e => e.error_type === 'structural').length },
    { label: 'Форматирования', value: errs.filter(e => e.error_type === 'formatting').length },
  ]
})

const formattedDate = computed(() => {
  if (!report.value?.timestamp) return '—'
  try {
    return new Date(report.value.timestamp).toLocaleString('ru-RU', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return report.value.timestamp
  }
})

const groupedErrors = computed(() => {
  const errs = errors.value
  return reactive({
    structural: { label: 'Структура',      errors: errs.filter(e => e.error_type === 'structural'), open: false },
    formatting: { label: 'Форматирование', errors: errs.filter(e => e.error_type === 'formatting'), open: false },
    content:    { label: 'Содержание',     errors: errs.filter(e => e.error_type === 'content'),    open: false },
    typography: { label: 'Типографика',    errors: errs.filter(e => e.error_type === 'typography'), open: false },
  })
})

// ── Helpers ────────────────────────────────────────────────────────────────────
const sevEmoji       = (s) => ({ critical: '🔴', high: '🟠', medium: '🟡', low: '🟢' }[s] ?? '⚪')
const bySev          = (errs, sev) => errs.filter(e => e.severity === sev)
const sevBorderClass = (sev) => ({
  critical: 'border-l-red-500',
  high:     'border-l-orange-400',
  medium:   'border-l-yellow-400',
  low:      'border-l-green-400',
}[sev] ?? 'border-l-gray-300')

// ── File handling ──────────────────────────────────────────────────────────────
function onDrop(e) {
  dragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) loadFile(file)
}

function onFileInput(e) {
  const file = e.target.files[0]
  if (file) loadFile(file)
  e.target.value = ''
}

function loadFile(file) {
  parseError.value = ''
  report.value     = null

  if (!file.name.endsWith('.json')) {
    parseError.value = 'Неверный формат файла. Ожидается .json'
    return
  }

  loadedFileName.value = file.name

  const reader = new FileReader()
  reader.onload = (ev) => {
    try {
      const parsed = JSON.parse(ev.target.result)

      // Accept both bare result object and full report wrapper
      if (parsed.result && parsed.document !== undefined) {
        // Full report from downloadReport()
        report.value = parsed
      } else if (parsed.errors !== undefined) {
        // Bare result object — wrap it
        report.value = {
          document:  file.name.replace('.json', ''),
          template:  '—',
          model:     '—',
          timestamp: new Date().toISOString(),
          result:    parsed,
        }
      } else {
        parseError.value = 'Файл не является корректным отчётом проверки документов.'
      }
    } catch {
      parseError.value = 'Не удалось разобрать JSON. Проверьте, что файл не повреждён.'
    }
  }
  reader.readAsText(file)
}

function clearReport() {
  report.value         = null
  parseError.value     = ''
  loadedFileName.value = ''
}
</script>
