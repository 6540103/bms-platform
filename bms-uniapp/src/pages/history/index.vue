<template>
  <view class="history-page">
    <!-- 时间范围选择 -->
    <view class="card">
      <view class="card-title">时间范围</view>
      <view class="time-tabs">
        <view v-for="tab in timeTabs" :key="tab.value" class="time-tab" :class="{ active: currentTab === tab.value }" @click="switchTab(tab.value)">
          {{ tab.label }}
        </view>
      </view>
    </view>

    <!-- 趋势图 -->
    <view class="card">
      <view class="card-title">数据趋势</view>
      <view class="chart-type-tabs">
        <view v-for="type in chartTypes" :key="type.value" class="chart-type-tab" :class="{ active: currentChart === type.value }" @click="currentChart = type.value">
          {{ type.label }}
        </view>
      </view>
      <view class="trend-chart">
        <view v-for="(item, i) in trendChartData" :key="i" class="trend-bar-item">
          <view class="trend-bar" :style="{ height: item.height + '%' }"></view>
          <text class="trend-bar-label">{{ item.label }}</text>
          <text class="trend-bar-value">{{ item.value }}</text>
        </view>
      </view>
    </view>

    <!-- 数据列表 -->
    <view class="card">
      <view class="card-title">数据记录 ({{ total }}条)</view>
      <view class="data-list">
        <view v-for="item in list" :key="item.id" class="data-item" @click="showDetail(item)">
          <view class="data-time">{{ formatTime(item.createTime) }}</view>
          <view class="data-main">
            <view class="data-row">
              <text class="data-label">电压</text>
              <text class="data-value">{{ item.packVoltage?.toFixed(2) }}V</text>
            </view>
            <view class="data-row">
              <text class="data-label">电流</text>
              <text class="data-value">{{ item.current?.toFixed(1) }}A</text>
            </view>
            <view class="data-row">
              <text class="data-label">SOC</text>
              <text class="data-value soc">{{ item.soc?.toFixed(1) }}%</text>
            </view>
            <view class="data-row">
              <text class="data-label">温度</text>
              <text class="data-value">{{ item.temperature?.toFixed(1) }}°C</text>
            </view>
          </view>
          <view class="data-status" :class="getStatusClass(item.status)">
            {{ getStatusText(item.status) }}
          </view>
        </view>
      </view>
      <view v-if="loading" class="loading-text">加载中...</view>
      <view v-if="!loading && list.length === 0" class="empty-text">暂无数据</view>
      <view v-if="hasMore && !loading" class="load-more" @click="loadMore">加载更多</view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDataList, statusMap } from '@/api/bms.js'

const timeTabs = [
  { label: '最近1小时', value: '1h' },
  { label: '今天', value: 'today' },
  { label: '最近7天', value: '7d' }
]

const chartTypes = [
  { label: '电压', value: 'voltage' },
  { label: '电流', value: 'current' },
  { label: 'SOC', value: 'soc' },
  { label: '温度', value: 'temp' }
]

const currentTab = ref('1h')
const currentChart = ref('voltage')
const list = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const hasMore = ref(true)

const trendChartData = ref([])

function switchTab(tab) {
  currentTab.value = tab
  pageNum.value = 1
  list.value = []
  hasMore.value = true
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getDataList({ pageNum: pageNum.value, pageSize: pageSize.value })
    if (res.code === 200) {
      const rows = res.rows || []
      if (pageNum.value === 1) {
        list.value = rows
      } else {
        list.value = [...list.value, ...rows]
      }
      total.value = res.total || 0
      hasMore.value = list.value.length < total.value
      updateChart(rows)
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function updateChart(rows) {
  const data = rows.slice(0, 10).reverse()
  let maxVal = 1
  let unit = ''
  const values = data.map(d => {
    switch (currentChart.value) {
      case 'voltage': unit = 'V'; return d.packVoltage || 0
      case 'current': unit = 'A'; return d.current || 0
      case 'soc': unit = '%'; return d.soc || 0
      case 'temp': unit = '°C'; return d.temperature || 0
      default: return 0
    }
  })
  maxVal = Math.max(...values, 1)
  trendChartData.value = data.map((d, i) => ({
    label: d.createTime?.slice(11, 16) || '',
    value: values[i].toFixed(1) + unit,
    height: Math.max(5, (values[i] / maxVal) * 100)
  }))
}

function loadMore() {
  pageNum.value++
  fetchData()
}

function formatTime(time) {
  if (!time) return '--'
  return time.slice(5, 16)
}

function getStatusClass(status) {
  return `status-${status || 'resting'}`
}

function getStatusText(status) {
  return statusMap[status]?.text || status || '--'
}

function showDetail(item) {
  uni.showModal({
    title: '数据详情',
    content: `时间: ${item.createTime}\n电压: ${item.packVoltage}V\n电流: ${item.current}A\nSOC: ${item.soc}%\n温度: ${item.temperature}°C\n状态: ${getStatusText(item.status)}`,
    showCancel: false
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.history-page { padding-bottom: 40rpx; }
.time-tabs { display: flex; gap: 12rpx; }
.time-tab {
  flex: 1;
  text-align: center;
  padding: 16rpx;
  border-radius: 12rpx;
  font-size: 24rpx;
  color: #8b8b9e;
  background: rgba(255, 255, 255, 0.03);
}
.time-tab.active {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
  border: 1rpx solid rgba(0, 212, 255, 0.3);
}
.chart-type-tabs { display: flex; gap: 8rpx; margin-bottom: 16rpx; flex-wrap: wrap; }
.chart-type-tab {
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
  color: #8b8b9e;
  background: rgba(255, 255, 255, 0.03);
}
.chart-type-tab.active { background: rgba(0, 212, 255, 0.2); color: #00d4ff; }
.chart-container { height: 350rpx; }
.data-list { display: flex; flex-direction: column; gap: 12rpx; }
.data-item {
  display: flex;
  padding: 16rpx;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12rpx;
}
.data-time { font-size: 22rpx; color: #8b8b9e; width: 120rpx; flex-shrink: 0; }
.data-main { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 8rpx; }
.data-row { display: flex; justify-content: space-between; }
.data-label { font-size: 22rpx; color: #8b8b9e; }
.data-value { font-size: 24rpx; color: #e0e0e0; font-weight: 500; }
.data-value.soc { color: #00d4ff; }
.data-status { font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 8rpx; align-self: flex-start; }
.status-discharging { background: rgba(255, 152, 0, 0.2); color: #ff9800; }
.status-charging { background: rgba(0, 200, 83, 0.2); color: #00c853; }
.status-resting { background: rgba(158, 158, 158, 0.2); color: #9e9e9e; }
.status-error { background: rgba(255, 82, 82, 0.2); color: #ff5252; }
.loading-text, .empty-text { text-align: center; padding: 24rpx; color: #8b8b9e; font-size: 24rpx; }
.load-more { text-align: center; padding: 20rpx; color: #00d4ff; font-size: 24rpx; }
.trend-chart { display: flex; align-items: flex-end; justify-content: space-between; height: 250rpx; padding: 16rpx 0; gap: 4rpx; }
.trend-bar-item { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
.trend-bar { width: 100%; max-width: 40rpx; border-radius: 4rpx 4rpx 0 0; min-height: 8rpx; background: linear-gradient(180deg, #00d4ff, #0097a7); }
.trend-bar-label { font-size: 16rpx; color: #8b8b9e; margin-top: 4rpx; }
.trend-bar-value { font-size: 14rpx; color: #b0b0b0; }
</style>
