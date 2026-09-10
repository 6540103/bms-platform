<template>
  <view class="dashboard">
    <!-- 顶部状态栏 -->
    <view class="status-bar">
      <view class="status-left">
        <view class="status-badge" :class="bmsStatusClass">{{ bmsStatusText }}</view>
        <view class="status-badge" :style="{ background: batteryStatusBg, color: batteryStatusColor, borderColor: batteryStatusColor }">
          {{ batteryStatusText }}
        </view>
      </view>
      <view class="status-right">
        <text class="update-time">更新: {{ updateTime }}</text>
      </view>
    </view>

    <!-- 告警横幅 -->
    <view v-if="hasAlarm" class="alarm-banner alarm">
      <text class="alarm-text">⚠ {{ alarmMessage }}</text>
    </view>
    <view v-else-if="hasWarning" class="alarm-banner warning">
      <text class="alarm-text">⚡ {{ warningMessage }}</text>
    </view>

    <!-- SOC 大卡片 -->
    <view class="soc-card">
      <view class="soc-main">
        <text class="soc-value">{{ data.soc?.toFixed(1) || '--' }}</text>
        <text class="soc-unit">%</text>
      </view>
      <view class="soc-label">SOC (EKF估算)</view>
      <view class="soc-compare">
        <text class="soc-compare-item">库仑: {{ coulombSoc }}%</text>
        <text class="soc-compare-item">OCV: {{ ocvSoc }}%</text>
      </view>
      <!-- SOC 进度条 -->
      <view class="soc-progress">
        <view class="soc-progress-fill" :style="{ width: (data.soc || 0) + '%' }"></view>
      </view>
    </view>

    <!-- 核心数据网格 -->
    <view class="data-grid">
      <view class="data-card">
        <view class="data-value">{{ data.packVoltage?.toFixed(2) || '--' }}<text class="data-unit">V</text></view>
        <view class="data-label">总电压</view>
      </view>
      <view class="data-card">
        <view class="data-value" :class="{ 'text-positive': (data.current || 0) > 0, 'text-negative': (data.current || 0) < 0 }">
          {{ data.current?.toFixed(1) || '--' }}<text class="data-unit">A</text>
        </view>
        <view class="data-label">电流</view>
      </view>
      <view class="data-card">
        <view class="data-value">{{ data.power?.toFixed(0) || '--' }}<text class="data-unit">W</text></view>
        <view class="data-label">功率</view>
      </view>
      <view class="data-card">
        <view class="data-value">{{ data.soh?.toFixed(1) || '--' }}<text class="data-unit">%</text></view>
        <view class="data-label">SOH健康度</view>
      </view>
      <view class="data-card">
        <view class="data-value">{{ data.temperature?.toFixed(1) || '--' }}<text class="data-unit">°C</text></view>
        <view class="data-label">电池温度</view>
      </view>
      <view class="data-card">
        <view class="data-value">{{ data.ambientTemp?.toFixed(1) || '--' }}<text class="data-unit">°C</text></view>
        <view class="data-label">环境温度</view>
      </view>
    </view>

    <!-- 电压不均衡卡片 -->
    <view class="card">
      <view class="card-title">单体电压</view>
      <view class="voltage-summary">
        <view class="voltage-item">
          <text class="voltage-label">最低</text>
          <text class="voltage-value low">{{ data.minCellVoltage?.toFixed(3) || '--' }}V</text>
        </view>
        <view class="voltage-item">
          <text class="voltage-label">最高</text>
          <text class="voltage-value high">{{ data.maxCellVoltage?.toFixed(3) || '--' }}V</text>
        </view>
        <view class="voltage-item">
          <text class="voltage-label">压差</text>
          <text class="voltage-value">{{ ((data.voltageImbalance || 0) * 1000).toFixed(0) }}mV</text>
        </view>
      </view>
      <view class="cell-bars">
        <view v-for="(v, i) in cellVoltages" :key="i" class="cell-bar-item">
          <view class="cell-bar-fill" :class="getCellVoltageClass(v)" :style="{ height: getCellBarHeight(v) + '%' }"></view>
          <text class="cell-bar-label">{{ i + 1 }}</text>
        </view>
      </view>
    </view>

    <!-- 趋势图 -->
    <view class="card">
      <view class="card-title">电压/电流/SOC 趋势</view>
      <view class="chart-container">
        <qiun-data-charts
          type="line"
          :opts="chartOpts"
          :chartData="chartData"
          :canvas2d="true"
        />
      </view>
    </view>

    <!-- BMS 状态详情 -->
    <view class="card">
      <view class="card-title">BMS 状态</view>
      <view class="bms-detail">
        <view class="bms-detail-row">
          <text class="bms-detail-label">保护状态</text>
          <text class="bms-detail-value" :class="protectionStatusClass">{{ protectionStatusText }}</text>
        </view>
        <view class="bms-detail-row">
          <text class="bms-detail-label">均衡状态</text>
          <text class="bms-detail-value" :class="balancingActive ? 'text-warning' : 'text-normal'">
            {{ balancingActive ? '均衡中' : '未均衡' }}
          </text>
        </view>
        <view class="bms-detail-row">
          <text class="bms-detail-label">充电允许</text>
          <text class="bms-detail-value" :class="chargeAllowed ? 'text-normal' : 'text-alarm'">
            {{ chargeAllowed ? '允许' : '禁止' }}
          </text>
        </view>
        <view class="bms-detail-row">
          <text class="bms-detail-label">放电允许</text>
          <text class="bms-detail-value" :class="dischargeAllowed ? 'text-normal' : 'text-alarm'">
            {{ dischargeAllowed ? '允许' : '禁止' }}
          </text>
        </view>
        <view class="bms-detail-row">
          <text class="bms-detail-label">循环次数</text>
          <text class="bms-detail-value">{{ data.cycleCount || 0 }}</text>
        </view>
        <view class="bms-detail-row">
          <text class="bms-detail-label">仿真时间</text>
          <text class="bms-detail-value">{{ formatSimTime(data.simTime) }}</text>
        </view>
      </view>
    </view>

    <!-- 底部刷新按钮 -->
    <view class="refresh-bar">
      <button class="refresh-btn" @click="fetchData" :loading="loading">
        {{ loading ? '刷新中...' : '手动刷新' }}
      </button>
      <text class="refresh-hint">自动刷新间隔: {{ refreshInterval / 1000 }}秒</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { getLatestData, getDataList, parseCellVoltage, parseBmsStatus, statusMap, bmsStatusMap } from '@/api/bms.js'

const data = ref({})
const loading = ref(false)
const updateTime = ref('--')
const refreshInterval = ref(3000)
let timer = null

// 历史数据用于趋势图
const historyData = ref([])
const maxHistoryPoints = 30

// 图表配置
const chartOpts = ref({
  color: ['#00d4ff', '#ff9800', '#00c853'],
  padding: [15, 15, 0, 5],
  enableScroll: false,
  legend: {
    show: true,
    position: 'bottom',
    fontSize: 10
  },
  xAxis: {
    disableGrid: true,
    labelCount: 5,
    fontSize: 9
  },
  yAxis: {
    gridType: 'dash',
    dashLength: 4,
    splitNumber: 3,
    fontSize: 9
  },
  extra: {
    line: {
      type: 'curve',
      width: 2,
      activeType: 'hollow'
    }
  }
})

const chartData = ref({
  categories: [],
  series: [
    { name: '电压(V)', data: [] },
    { name: '电流(A)', data: [] },
    { name: 'SOC(%)', data: [] }
  ]
})

// 计算属性
const cellVoltages = computed(() => parseCellVoltage(data.value.cellVoltage))

const bmsStatusObj = computed(() => parseBmsStatus(data.value.bmsStatus))

const bmsStatusText = computed(() => {
  const status = bmsStatusObj.value?.bms_status || 'normal'
  return bmsStatusMap[status]?.text || '正常'
})

const bmsStatusClass = computed(() => {
  const status = bmsStatusObj.value?.bms_status || 'normal'
  return bmsStatusMap[status]?.class || 'status-normal'
})

const batteryStatusText = computed(() => statusMap[data.value.status]?.text || '未知')
const batteryStatusBg = computed(() => statusMap[data.value.status] ? `${statusMap[data.value.status].color}22` : 'rgba(158,158,158,0.2)')
const batteryStatusColor = computed(() => statusMap[data.value.status]?.color || '#9e9e9e')

const coulombSoc = computed(() => {
  const val = bmsStatusObj.value?.soc?.coulomb
  return val !== undefined ? (val * 100).toFixed(1) : '--'
})

const ocvSoc = computed(() => {
  const val = bmsStatusObj.value?.soc?.ocv
  return val !== undefined ? (val * 100).toFixed(1) : '--'
})

const hasAlarm = computed(() => {
  const protections = bmsStatusObj.value?.protection?.alarms || []
  return protections.length > 0
})

const hasWarning = computed(() => {
  const warnings = bmsStatusObj.value?.protection?.warnings || []
  return warnings.length > 0 && !hasAlarm.value
})

const alarmMessage = computed(() => {
  const alarms = bmsStatusObj.value?.protection?.alarms || []
  return alarms.join(', ')
})

const warningMessage = computed(() => {
  const warnings = bmsStatusObj.value?.protection?.warnings || []
  return warnings.join(', ')
})

const protectionStatusText = computed(() => {
  const status = bmsStatusObj.value?.protection?.fault_status || 'normal'
  return bmsStatusMap[status]?.text || '正常'
})

const protectionStatusClass = computed(() => {
  const status = bmsStatusObj.value?.protection?.fault_status || 'normal'
  return bmsStatusMap[status]?.class || 'status-normal'
})

const balancingActive = computed(() => bmsStatusObj.value?.balancing?.active || false)
const chargeAllowed = computed(() => bmsStatusObj.value?.protection?.charge_allowed !== false)
const dischargeAllowed = computed(() => bmsStatusObj.value?.protection?.discharge_allowed !== false)

// 方法
function getCellVoltageClass(v) {
  if (v < 3.2) return 'cell-low'
  if (v > 4.15) return 'cell-high'
  return 'cell-normal'
}

function getCellBarHeight(v) {
  const min = 3.0, max = 4.2
  const percent = ((v - min) / (max - min)) * 100
  return Math.max(10, Math.min(100, percent))
}

function formatSimTime(seconds) {
  if (!seconds) return '--'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}分${s}秒`
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getLatestData()
    if (res.code === 200 && res.data) {
      data.value = res.data
      updateTime.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })

      // 添加到历史数据
      historyData.value.push(res.data)
      if (historyData.value.length > maxHistoryPoints) {
        historyData.value.shift()
      }
      updateChart()
    }
  } catch (e) {
    console.error('获取数据失败', e)
  } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
}

function updateChart() {
  const categories = historyData.value.map((_, i) => `t${i + 1}`)
  const voltage = historyData.value.map(d => d.packVoltage?.toFixed(1) || 0)
  const current = historyData.value.map(d => d.current?.toFixed(1) || 0)
  const soc = historyData.value.map(d => d.soc?.toFixed(1) || 0)

  chartData.value = {
    categories,
    series: [
      { name: '电压(V)', data: voltage },
      { name: '电流(A)', data: current },
      { name: 'SOC(%)', data: soc }
    ]
  }
}

function startAutoRefresh() {
  stopAutoRefresh()
  timer = setInterval(fetchData, refreshInterval.value)
}

function stopAutoRefresh() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onPullDownRefresh(() => {
  fetchData()
})

onMounted(() => {
  fetchData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.dashboard {
  padding-bottom: 40rpx;
}

.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 24rpx;
}

.status-left {
  display: flex;
  gap: 16rpx;
}

.update-time {
  font-size: 22rpx;
  color: #8b8b9e;
}

.alarm-banner {
  margin: 0 24rpx 16rpx;
  padding: 16rpx 24rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
}

.alarm-banner.alarm {
  background: rgba(255, 82, 82, 0.15);
  border: 1rpx solid rgba(255, 82, 82, 0.3);
}

.alarm-banner.warning {
  background: rgba(255, 171, 0, 0.15);
  border: 1rpx solid rgba(255, 171, 0, 0.3);
}

.alarm-text {
  font-size: 24rpx;
  color: #fff;
}

.soc-card {
  margin: 16rpx 24rpx;
  padding: 32rpx;
  background: linear-gradient(135deg, #0d47a1 0%, #1565c0 50%, #00bcd4 100%);
  border-radius: 20rpx;
  text-align: center;
}

.soc-main {
  display: flex;
  align-items: baseline;
  justify-content: center;
}

.soc-value {
  font-size: 96rpx;
  font-weight: 800;
  color: #fff;
  line-height: 1;
}

.soc-unit {
  font-size: 36rpx;
  color: rgba(255, 255, 255, 0.8);
  margin-left: 8rpx;
}

.soc-label {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 8rpx;
}

.soc-compare {
  display: flex;
  justify-content: center;
  gap: 32rpx;
  margin-top: 16rpx;
}

.soc-compare-item {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.6);
}

.soc-progress {
  height: 12rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6rpx;
  margin-top: 20rpx;
  overflow: hidden;
}

.soc-progress-fill {
  height: 100%;
  background: #fff;
  border-radius: 6rpx;
  transition: width 0.5s ease;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16rpx;
  padding: 0 24rpx;
}

.data-card {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 16rpx;
  padding: 20rpx;
  border: 1rpx solid rgba(0, 212, 255, 0.1);
}

.text-positive {
  color: #ff9800 !important;
}

.text-negative {
  color: #00c853 !important;
}

.voltage-summary {
  display: flex;
  justify-content: space-around;
  margin-bottom: 20rpx;
}

.voltage-item {
  text-align: center;
}

.voltage-label {
  display: block;
  font-size: 22rpx;
  color: #8b8b9e;
  margin-bottom: 4rpx;
}

.voltage-value {
  font-size: 28rpx;
  font-weight: 600;
  color: #fff;
}

.voltage-value.low {
  color: #ff5252;
}

.voltage-value.high {
  color: #ffab00;
}

.cell-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 120rpx;
  padding: 0 8rpx;
}

.cell-bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 5%;
}

.cell-bar-fill {
  width: 100%;
  border-radius: 4rpx 4rpx 0 0;
  min-height: 8rpx;
}

.cell-bar-fill.cell-normal {
  background: linear-gradient(180deg, #00d4ff, #0097a7);
}

.cell-bar-fill.cell-low {
  background: linear-gradient(180deg, #ff5252, #c62828);
}

.cell-bar-fill.cell-high {
  background: linear-gradient(180deg, #ffab00, #ff6f00);
}

.cell-bar-label {
  font-size: 16rpx;
  color: #8b8b9e;
  margin-top: 4rpx;
}

.chart-container {
  height: 400rpx;
}

.bms-detail-row {
  display: flex;
  justify-content: space-between;
  padding: 12rpx 0;
  border-bottom: 1rpx solid rgba(255, 255, 255, 0.05);
}

.bms-detail-row:last-child {
  border-bottom: none;
}

.bms-detail-label {
  font-size: 26rpx;
  color: #8b8b9e;
}

.bms-detail-value {
  font-size: 26rpx;
  color: #e0e0e0;
  font-weight: 500;
}

.text-normal {
  color: #00c853 !important;
}

.text-warning {
  color: #ffab00 !important;
}

.text-alarm {
  color: #ff5252 !important;
}

.refresh-bar {
  padding: 24rpx;
  text-align: center;
}

.refresh-btn {
  background: linear-gradient(135deg, #00d4ff, #0097a7);
  color: #0f0f1a;
  font-weight: 600;
  border-radius: 40rpx;
  width: 80%;
  margin: 0 auto;
}

.refresh-hint {
  display: block;
  font-size: 22rpx;
  color: #8b8b9e;
  margin-top: 12rpx;
}
</style>
