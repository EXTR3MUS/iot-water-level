<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

const loading = ref(false)
const error = ref(null)
const buffer = ref([])

const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/'

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(BACKEND_URL)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    if (data && Array.isArray(data.buffer)) {
      buffer.value = data.buffer.slice().reverse()
    } else {
      buffer.value = []
    }
  } catch (err) {
    error.value = err?.message ?? String(err)
  } finally {
    loading.value = false
  }
}

// Live polling enabled - fetches data every 500ms
let timer = null
onMounted(() => {
  fetchData()
  timer = setInterval(fetchData, 500)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})

// Minimal hardcoded demo dataset for ApexCharts (easy to switch to for validation)
const demoSeries = [{
  name: 'Demo Water Level',
  data: [1.2, 1.5, 1.4, 1.8, 2.0]
}]

const demoChartOptions = {
  chart: {
    type: 'line',
    height: 260
  },
  xaxis: {
    categories: ['t1', 't2', 't3', 't4', 't5']
  },
  stroke: {
    curve: 'smooth',
    width: 2
  },
  colors: ['#42a5f5']
}

const values = computed(() => buffer.value.map((it) => Number(it.water_level)))
const labels = computed(() => buffer.value.map((it) => {
  try { return new Date(it.recorded_ts).toLocaleTimeString() } catch { return '' }
}))

// ApexCharts reactive series and options for live data
const liveSeries = ref([{
  name: 'Water Level',
  data: []
}])

const liveChartOptions = ref({
  chart: {
    type: 'line',
    height: 260,
    background: '#0b0f14',
    foreColor: '#e6eef8',
    animations: {
      enabled: false
    }
  },
  xaxis: {
    categories: [],
    labels: { style: { colors: '#bbb' } }
  },
  yaxis: {
    labels: { style: { colors: '#bbb' } }
  },
  stroke: {
    curve: 'straight',
    width: 2
  },
  colors: ['#4fc3f7'],
  grid: {
    borderColor: 'rgba(255,255,255,0.1)'
  },
  theme: {
    mode: 'dark'
  }
})

watch([values, labels], ([nv, nl]) => {
  liveSeries.value = [{ name: 'Water Level', data: nv }]
  liveChartOptions.value = { ...liveChartOptions.value, xaxis: { ...liveChartOptions.value.xaxis, categories: nl } }
})
</script>

<template>
  <div class="app-root">
    <h1>Water Level</h1>

    <p v-if="error" class="error">Error: {{ error }}</p>

    <!-- Live chart with ApexCharts -->
    <div class="chart-wrap">
      <div class="chart-container">
        <VueApexCharts type="line" height="260" :options="liveChartOptions" :series="liveSeries" />
      </div>
    </div>

    <div class="meta">
      <div>Latest: <strong>{{ values.length ? values[values.length-1] : '—' }}</strong></div>
      <div>Points: {{ values.length }}</div>
    </div>

    <!-- Demo chart (commented out - uncomment to test hardcoded data) -->
    <!--
    <div class="demo-wrap">
      <div class="demo-chart-container">
        <VueApexCharts type="line" height="260" :options="demoChartOptions" :series="demoSeries" />
      </div>
      <div class="demo-meta">Demo dataset (hardcoded) - use this to validate ApexCharts</div>
    </div>
    -->
  </div>
</template>

<style scoped>
.app-root { background: #0b0f14; color: #e6eef8; padding: 16px; border-radius: 6px; }
.chart-wrap { margin-top: 12px; }
.chart-container { height: 280px; background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding: 12px; border-radius: 6px; }
.error { color: #ff6b6b; }
.meta { margin-top: 8px; display:flex; gap:12px; color: #cfe8ff }
h1 { margin: 0 0 8px 0; color: #dff4ff }

/* Demo-specific light styles */
.demo-wrap { margin-top: 12px; }
.demo-chart-container { height: 260px; background: #fff; color: #000; padding: 12px; border-radius: 6px; }
.demo-meta { margin-top: 8px; color: #333 }
</style>
