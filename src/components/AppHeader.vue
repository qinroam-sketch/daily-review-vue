<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
</script>
<template>
  <header class="app-header">
    <div class="inner">
      <router-link class="brand" to="/">
        <span class="mark">复</span>
        <span>
          A股每日复盘
          <small>短线情绪 · 龙虎榜 · 题材</small>
        </span>
      </router-link>
      <nav class="nav-links">
        <router-link to="/" :class="{ active: route.name === 'home' }">交易日</router-link>
        <router-link to="/week" :class="{ active: route.name === 'week' }">一周复盘</router-link>
      </nav>
    </div>
  </header>
</template>
