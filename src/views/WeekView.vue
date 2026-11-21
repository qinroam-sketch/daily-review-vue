<script setup>
import Disclaimer from '../components/Disclaimer.vue'
</script>
<template>
  <main class="page">
    <h1 class="page-title">一周复盘</h1>
    <p class="page-sub">周总结会在按周批量更新后提供。当前仓库先放了 8 月 3 日这一天的样板，用来确认格式。</p>
    <div class="stub">
      <p>这里以后会放「一周主线、情绪节奏、龙虎榜资金偏好」的对照。</p>
      <p>
        先看单日样板：
        <router-link to="/day/2026-08-03">2026-08-03 每日复盘</router-link>
      </p>
    </div>
    <Disclaimer />
  </main>
</template>
