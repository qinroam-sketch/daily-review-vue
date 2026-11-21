<script setup>
defineProps({ extra: { type: String, default: '' } })
</script>
<template>
  <div class="foot">基于数据的分析框架，不构成投资建议</div>
  <div v-if="extra" class="foot-sub">{{ extra }}</div>
</template>
