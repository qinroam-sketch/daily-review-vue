<script setup>
defineProps({
  title: { type: String, default: '白话解读' },
  notes: { type: Array, default: () => [] },
})
</script>
<template>
  <div v-if="notes && notes.length" class="note">
    <div class="lab">{{ title }}</div>
    <p v-for="(n, i) in notes" :key="i">{{ n }}</p>
  </div>
</template>
