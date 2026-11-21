<script setup>
defineProps({ text: { type: String, default: '' } })
</script>
<template>
  <p v-if="text" class="src">{{ text }}</p>
</template>
