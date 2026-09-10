<template>
  <view class="battery-page">
    <!-- 概览卡片 -->
    <view class="card">
      <view class="card-title">电池概览</view>
      <view class="overview-grid">
        <view class="overview-item">
          <text class="overview-value">{{ data.packVoltage?.toFixed(2) || '--' }}</text>
          <text class="overview-unit">V</text>
          <text class="overview-label">总电压</text>
        </view>
        <view class="overview-item">
          <text class="overview-value">{{ data.soc?.toFixed(1) || '--' }}</text>
          <text class="overview-unit">%</text>
          <text class="overview-label">SOC</text>
        </view>
        <view class="overview-item">
          <text class="overview-value">{{ data.temperature?.toFixed(1) || '--' }}</text>
          <text class="overview-unit">°C</text>
          <text class="overview-label">温度</text>
        </view>
        <view class="overview-item">
          <text class="overview-value">{{ ((data.voltageImbalance || 0) * 1000).toFixed(0) }}</text>
          <text class="overview-unit">mV</text>
          <text class="overview-label">压差</text>
        </view>
      </view>
    </view>

    <!-- 单体电压柱状图 -->
    <view class="card">
      <view class="card-title">单体电压分布 (13S)</view>
      <view class="css-chart">
        <view v-for="(v, i) in cellVoltages" :key="i" class="css-bar-item">
          <view class="css-bar" :style="{ height: getBarHeight(v) + '%' }" :class="getBarClass(v)"></view>
          <text class="css-bar-label">{{ i + 1 }}</text>
        </view>
      </view>
    </view>

    <!-- 单体详情列表 -->
    <view class="card">
      <view class="card-title">单体详情</view>
      <view class="cell-list">
        <view v-for="(cell, index) in cellList" :key="index" class="cell-item" :class="cell.statusClass">
          <view class="cell-index">{{ index + 1 }}</view>
          <view class="cell-info">
            <view class="cell-voltage">{{ cell.voltage.toFixed(3) }} V</view>
            <view class="cell-soc">SOC: {{ cell.soc?.toFixed(1) || '--' }}%</view>
          </view>
          <view class="cell-status">
            <text class="cell-status-text">{{ cell.statusText }}</text>
          </view>
          <view class="cell-bar">
            <view class="cell-bar-fill" :style="{ width: cell.percent + '%' }" :class="cell.statusClass"></view>
          </view>
        </view>
      </view>
    </view>

    <!-- 最低/最高高亮 -->
    <view class="card">
      <view class="card-title">极值统计</view>
      <view class="extreme-grid">
        <view class="extreme-item low">
          <text class="extreme-label">最低单体</text>
          <text class="extreme-value">#{{ minCellIndex + 1 }}</text>
          <text class="extreme-voltage">{{ data.minCellVoltage?.toFixed(3) || '--' }} V</text>
        </view>
        <view class="extreme-item high">
          <text class="extreme-label">最高单体</text>
          <text class="extreme-value">#{{ maxCellIndex + 1 }}</text>
          <text class="extreme-voltage">{{ data.maxCellVoltage?.toFixed(3) || '--' }} V</text>
        </view>
      </view>
    </view>

    <view class="refresh-bar">
      <button class="refresh-btn" @click="fetchData" :loading="loading">刷新数据</button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getLatestData, parseCellVoltage, parseCellSoc } from '@/api/bms.js'

const data = ref({})
const loading = ref(false)

function getBarHeight(v) {
  return Math.max(10, Math.min(100, ((v - 3.0) / 1.2) * 100))
}

function getBarClass(v) {
  if (v < 3.2) return 'bar-low'
  if (v > 4.15) return 'bar-high'
  return 'bar-normal'
}

const cellVoltages = computed(() => parseCellVoltage(data.value.cellVoltage))
const cellSocs = computed(() => parseCellSoc(data.value.cellSoc))

const minCellIndex = computed(() => {
  const arr = cellVoltages.value
  if (!arr.length) return 0
  return arr.indexOf(Math.min(...arr))
})

const maxCellIndex = computed(() => {
  const arr = cellVoltages.value
  if (!arr.length) return 0
  return arr.indexOf(Math.max(...arr))
})

const cellList = computed(() => {
  return cellVoltages.value.map((v, i) => {
    let statusClass = 'cell-normal'
    let statusText = '正常'
    if (v < 3.2) {
      statusClass = 'cell-low'
      statusText = '偏低'
    } else if (v > 4.15) {
      statusClass = 'cell-high'
      statusText = '偏高'
    }
    const percent = ((v - 3.0) / 1.2) * 100
    return {
      voltage: v,
      soc: cellSocs.value[i],
      statusClass,
      statusText,
      percent: Math.max(5, Math.min(100, percent))
    }
  })
})

async function fetchData() {
  loading.value = true
  try {
    const res = await getLatestData()
    if (res.code === 200 && res.data) {
      data.value = res.data
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}



onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.battery-page { padding-bottom: 40rpx; }
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
}
.overview-item { text-align: center; }
.overview-value { font-size: 36rpx; font-weight: 700; color: #00d4ff; }
.overview-unit { font-size: 20rpx; color: #8b8b9e; margin-left: 4rpx; }
.overview-label { display: block; font-size: 22rpx; color: #8b8b9e; margin-top: 4rpx; }
.chart-container { height: 350rpx; }
.cell-list { display: flex; flex-direction: column; gap: 12rpx; }
.cell-item {
  display: flex;
  align-items: center;
  padding: 16rpx;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12rpx;
  border-left: 6rpx solid #00d4ff;
}
.cell-item.cell-low { border-left-color: #ff5252; }
.cell-item.cell-high { border-left-color: #ffab00; }
.cell-index {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 600;
  margin-right: 16rpx;
}
.cell-info { flex: 1; }
.cell-voltage { font-size: 28rpx; font-weight: 600; color: #fff; }
.cell-soc { font-size: 22rpx; color: #8b8b9e; margin-top: 2rpx; }
.cell-status { margin-right: 16rpx; }
.cell-status-text { font-size: 22rpx; padding: 4rpx 12rpx; border-radius: 8rpx; background: rgba(0, 200, 83, 0.2); color: #00c853; }
.cell-low .cell-status-text { background: rgba(255, 82, 82, 0.2); color: #ff5252; }
.cell-high .cell-status-text { background: rgba(255, 171, 0, 0.2); color: #ffab00; }
.cell-bar { width: 120rpx; height: 12rpx; background: rgba(255, 255, 255, 0.1); border-radius: 6rpx; overflow: hidden; }
.cell-bar-fill { height: 100%; border-radius: 6rpx; background: #00d4ff; }
.cell-bar-fill.cell-low { background: #ff5252; }
.cell-bar-fill.cell-high { background: #ffab00; }
.extreme-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16rpx; }
.extreme-item { padding: 20rpx; border-radius: 12rpx; text-align: center; }
.extreme-item.low { background: rgba(255, 82, 82, 0.1); border: 1rpx solid rgba(255, 82, 82, 0.3); }
.extreme-item.high { background: rgba(255, 171, 0, 0.1); border: 1rpx solid rgba(255, 171, 0, 0.3); }
.extreme-label { display: block; font-size: 22rpx; color: #8b8b9e; }
.extreme-value { display: block; font-size: 40rpx; font-weight: 700; color: #fff; margin: 8rpx 0; }
.extreme-voltage { font-size: 26rpx; font-weight: 600; }
.low .extreme-voltage { color: #ff5252; }
.high .extreme-voltage { color: #ffab00; }
.refresh-bar { padding: 24rpx; text-align: center; }
.css-chart { display: flex; align-items: flex-end; justify-content: space-between; height: 250rpx; padding: 16rpx 0; gap: 4rpx; }
.css-bar-item { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
.css-bar { width: 100%; max-width: 40rpx; border-radius: 4rpx 4rpx 0 0; min-height: 8rpx; background: #00d4ff; }
.css-bar.bar-low { background: #ff5252; }
.css-bar.bar-high { background: #ffab00; }
.css-bar-label { font-size: 18rpx; color: #8b8b9e; margin-top: 4rpx; }
.refresh-btn {
  background: linear-gradient(135deg, #00d4ff, #0097a7);
  color: #0f0f1a;
  font-weight: 600;
  border-radius: 40rpx;
  width: 80%;
  margin: 0 auto;
}
</style>
