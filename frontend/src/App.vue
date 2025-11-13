<script setup>
import { ref, computed } from 'vue'

const loading = ref(false)            // boolean: true while the request is in progress
const error = ref(null)               // string | null: stores error message
const responseData = ref(null)        // object | null: stores parsed JSON response

async function fetchData() {
  loading.value = true                // mark loading start
  error.value = null                  // clear previous error
  responseData.value = null           // clear previous data

  try {
    const res = await fetch('http://localhost:8000/') // make request to backend
    if (!res.ok) throw new Error(`HTTP ${res.status}`) // propagate non-2xx
    responseData.value = await res.json()              // store JSON response
  } catch (err) {
    error.value = err?.message ?? String(err)          // set a readable error
  } finally {
    loading.value = false               // always clear loading flag
  }
}

const responseText = computed(() =>
  responseData.value ? JSON.stringify(responseData.value, null, 2) : ''
) // pretty-prints response for display
</script>

<template>
  <h1>Water Level</h1>
  <button @click="fetchData" :disabled="loading">
    {{ loading ? 'Loading…' : 'Fetch test data' }}
  </button>

  <p v-if="error" class="error">Error: {{ error }}</p>

  <pre v-if="responseData" class="response">{{ responseText }}</pre>
</template>

<style scoped></style>
