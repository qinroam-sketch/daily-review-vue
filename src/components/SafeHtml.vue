<script setup>
import { computed } from 'vue'
import { sanitize } from '../lib/safeHtml.js'
const props = defineProps({ html: { type: String, default: '' } })
const clean = computed(() => sanitize(props.html))
</script>
<template>
  <div class="summary" v-html="clean"></div>
</template>
