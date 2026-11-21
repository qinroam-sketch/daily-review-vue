<script setup>
defineProps({ tag: { type: String, default: '' } })
function kind(tag) {
  if (!tag) return 'tag-mute'
  if (tag.includes('高潮') || tag.includes('发酵')) return 'tag-red'
  if (tag.includes('冰点') || tag.includes('退潮')) return 'tag-green'
  if (tag.includes('修复') || tag.includes('分歧')) return 'tag-gold'
  return 'tag-blue'
}
</script>
<template>
  <span v-if="tag" class="tag" :class="kind(tag)">{{ tag }}</span>
</template>
