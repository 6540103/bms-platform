<template>
  <view class="settings-page">
    <!-- 刷新设置 -->
    <view class="card">
      <view class="card-title">刷新设置</view>
      <view class="setting-item">
        <view class="setting-info">
          <text class="setting-label">自动刷新间隔</text>
          <text class="setting-desc">实时监控页面数据刷新频率</text>
        </view>
        <picker :range="refreshOptions" :range-key="'label'" @change="onRefreshChange">
          <view class="setting-value">{{ currentRefreshLabel }}</view>
        </picker>
      </view>
      <view class="setting-item">
        <view class="setting-info">
          <text class="setting-label">自动刷新</text>
          <text class="setting-desc">开启后实时监控页面自动刷新</text>
        </view>
        <switch :checked="autoRefresh" @change="onAutoRefreshChange" color="#00d4ff" />
      </view>
    </view>

    <!-- API 设置 -->
    <view class="card">
      <view class="card-title">API 设置</view>
      <view class="setting-item">
        <view class="setting-info">
          <text class="setting-label">后端地址</text>
          <text class="setting-desc">BMS 后端 API 服务地址</text>
        </view>
      </view>
      <view class="api-input-group">
        <input class="api-input" v-model="apiBaseUrl" placeholder="http://192.168.1.26:8080" />
        <button class="api-test-btn" @click="testApi">测试连接</button>
      </view>
      <view class="api-status" :class="apiStatusClass">
        {{ apiStatusText }}
      </view>
    </view>

    <!-- 数据管理 -->
    <view class="card">
      <view class="card-title">数据管理</view>
      <view class="setting-item" @click="clearCache">
        <view class="setting-info">
          <text class="setting-label">清除缓存</text>
          <text class="setting-desc">清除本地缓存的电池数据</text>
        </view>
        <text class="setting-arrow">›</text>
      </view>
      <view class="setting-item" @click="exportData">
        <view class="setting-info">
          <text class="setting-label">导出数据</text>
          <text class="setting-desc">导出历史数据为 CSV</text>
        </view>
        <text class="setting-arrow">›</text>
      </view>
    </view>

    <!-- 关于 -->
    <view class="card">
      <view class="card-title">关于</view>
      <view class="about-section">
        <view class="about-logo">BMS</view>
        <view class="about-name">电池管理系统</view>
        <view class="about-version">版本 1.0.0</view>
        <view class="about-desc">
          基于 uni-app 开发的 BMS 移动端监控应用，支持实时监控电池状态、历史数据查询、告警记录等功能。
        </view>
      </view>
      <view class="about-info-list">
        <view class="about-info-item">
          <text class="about-info-label">技术栈</text>
          <text class="about-info-value">Vue 3 + uni-app + uView</text>
        </view>
        <view class="about-info-item">
          <text class="about-info-label">图表库</text>
          <text class="about-info-value">uCharts</text>
        </view>
        <view class="about-info-item">
          <text class="about-info-label">后端</text>
          <text class="about-info-value">Spring Boot + RuoYi</text>
        </view>
        <view class="about-info-item">
          <text class="about-info-label">电池类型</text>
          <text class="about-info-value">三元锂 13S 48V 40Ah</text>
        </view>
      </view>
    </view>

    <view class="footer">
      <text>BMS Mobile v1.0.0</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'

const refreshOptions = [
  { label: '2秒', value: 2000 },
  { label: '5秒', value: 5000 },
  { label: '10秒', value: 10000 },
  { label: '30秒', value: 30000 },
  { label: '手动', value: 0 }
]

const autoRefresh = ref(true)
const currentRefreshIndex = ref(1)
const apiBaseUrl = ref('http://192.168.1.26:8080')
const apiStatus = ref('idle')

const currentRefreshLabel = computed(() => refreshOptions[currentRefreshIndex.value].label)

const apiStatusClass = computed(() => {
  if (apiStatus.value === 'testing') return 'testing'
  if (apiStatus.value === 'success') return 'success'
  if (apiStatus.value === 'error') return 'error'
  return 'idle'
})

const apiStatusText = computed(() => {
  if (apiStatus.value === 'testing') return '正在测试连接...'
  if (apiStatus.value === 'success') return '✓ 连接成功'
  if (apiStatus.value === 'error') return '✗ 连接失败'
  return '未测试'
})

function onRefreshChange(e) {
  currentRefreshIndex.value = e.detail.value
  uni.setStorageSync('refreshInterval', refreshOptions[e.detail.value].value)
  uni.showToast({ title: '已设置刷新间隔', icon: 'success' })
}

function onAutoRefreshChange(e) {
  autoRefresh.value = e.detail.value
  uni.setStorageSync('autoRefresh', e.detail.value)
}

async function testApi() {
  apiStatus.value = 'testing'
  try {
    const res = await new Promise((resolve, reject) => {
      uni.request({
        url: apiBaseUrl.value + '/bms/realtime/latest',
        method: 'GET',
        success: resolve,
        fail: reject
      })
    })
    if (res.statusCode === 200) {
      apiStatus.value = 'success'
      uni.setStorageSync('apiBaseUrl', apiBaseUrl.value)
    } else {
      apiStatus.value = 'error'
    }
  } catch (e) {
    apiStatus.value = 'error'
  }
}

function clearCache() {
  uni.showModal({
    title: '确认清除',
    content: '确定要清除所有本地缓存数据吗？',
    success: (res) => {
      if (res.confirm) {
        uni.clearStorageSync()
        uni.showToast({ title: '缓存已清除', icon: 'success' })
      }
    }
  })
}

function exportData() {
  uni.showToast({ title: '导出功能开发中', icon: 'none' })
}
</script>

<style lang="scss" scoped>
.settings-page { padding-bottom: 40rpx; }
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1rpx solid rgba(255, 255, 255, 0.05);
}
.setting-item:last-child { border-bottom: none; }
.setting-info { flex: 1; }
.setting-label { display: block; font-size: 28rpx; color: #e0e0e0; }
.setting-desc { display: block; font-size: 22rpx; color: #8b8b9e; margin-top: 4rpx; }
.setting-value { font-size: 26rpx; color: #00d4ff; padding: 8rpx 20rpx; background: rgba(0, 212, 255, 0.1); border-radius: 8rpx; }
.setting-arrow { font-size: 32rpx; color: #8b8b9e; }
.api-input-group { display: flex; gap: 12rpx; margin-top: 16rpx; }
.api-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1rpx solid rgba(255, 255, 255, 0.1);
  border-radius: 8rpx;
  padding: 16rpx;
  font-size: 24rpx;
  color: #e0e0e0;
}
.api-test-btn {
  background: linear-gradient(135deg, #00d4ff, #0097a7);
  color: #0f0f1a;
  font-size: 24rpx;
  font-weight: 600;
  border-radius: 8rpx;
  padding: 0 24rpx;
  line-height: 72rpx;
}
.api-status { margin-top: 12rpx; font-size: 24rpx; padding: 12rpx; border-radius: 8rpx; text-align: center; }
.api-status.testing { background: rgba(255, 171, 0, 0.1); color: #ffab00; }
.api-status.success { background: rgba(0, 200, 83, 0.1); color: #00c853; }
.api-status.error { background: rgba(255, 82, 82, 0.1); color: #ff5252; }
.api-status.idle { background: rgba(255, 255, 255, 0.03); color: #8b8b9e; }
.about-section { text-align: center; padding: 24rpx 0; }
.about-logo {
  width: 120rpx;
  height: 120rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #00d4ff, #0097a7);
  color: #0f0f1a;
  font-size: 40rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16rpx;
}
.about-name { font-size: 32rpx; font-weight: 600; color: #fff; }
.about-version { font-size: 24rpx; color: #8b8b9e; margin-top: 4rpx; }
.about-desc { font-size: 24rpx; color: #b0b0b0; margin-top: 16rpx; line-height: 1.6; }
.about-info-list { margin-top: 24rpx; border-top: 1rpx solid rgba(255, 255, 255, 0.05); padding-top: 16rpx; }
.about-info-item { display: flex; justify-content: space-between; padding: 12rpx 0; }
.about-info-label { font-size: 24rpx; color: #8b8b9e; }
.about-info-value { font-size: 24rpx; color: #e0e0e0; }
.footer { text-align: center; padding: 32rpx; color: #5a5a6e; font-size: 22rpx; }
</style>
