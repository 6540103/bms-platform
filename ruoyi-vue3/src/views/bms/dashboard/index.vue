<template>
  <div class="bms-dashboard">
    <!-- 顶部标题栏 -->
    <div class="dashboard-header">
      <div class="header-left">
        <h1>电池管理系统 (BMS) - 实时监控</h1>
        <div class="header-badges">
          <el-tag :type="bmsStatusType" size="large" effect="dark">BMS: {{ bmsStatusText }}</el-tag>
          <el-tag :type="protectionType" size="large">保护: {{ protectionText }}</el-tag>
          <el-tag v-if="balancingActive" type="primary" size="large" effect="plain">均衡中</el-tag>
          <el-tag v-else type="info" size="large" effect="plain">均衡待机</el-tag>
        </div>
      </div>
      <div class="header-info">
        <el-tag :type="statusTagType" size="large">{{ statusText }}</el-tag>
        <span class="update-time">更新: {{ lastUpdateTime }}</span>
      </div>
    </div>

    <!-- 告警横幅 -->
    <el-alert v-if="activeAlarms.length > 0"
      :title="activeAlarms.join(' | ')"
      type="error" show-icon :closable="false" class="alert-banner" />
    <el-alert v-else-if="activeWarnings.length > 0"
      :title="activeWarnings.join(' | ')"
      type="warning" show-icon :closable="false" class="alert-banner" />

    <!-- 状态卡片行 -->
    <el-row :gutter="16" class="stat-cards">
      <el-col :xs="12" :sm="8" :md="4">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-label">总电压</div>
          <div class="stat-value">{{ latest.packVoltage ?? '--' }} <span class="stat-unit">V</span></div>
          <div class="stat-sub">{{ latest.minCellVoltage ?? '--' }} ~ {{ latest.maxCellVoltage ?? '--' }} V/单体</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-label">电流</div>
          <div class="stat-value" :class="currentClass">{{ latest.current ?? '--' }} <span class="stat-unit">A</span></div>
          <div class="stat-sub">{{ latest.power ?? '--' }} W</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-label">SOC (EKF)</div>
          <div class="stat-value soc-value">{{ latest.soc ?? '--' }} <span class="stat-unit">%</span></div>
          <div class="stat-sub soc-compare">
            库仑: {{ socCoulomb }}% | OCV: {{ socOcv }}%
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-label">SOH 健康度</div>
          <div class="stat-value soh-value">{{ latest.soh ?? '--' }} <span class="stat-unit">%</span></div>
          <div class="stat-sub">容量 {{ sohCapacity }}% | 内阻 {{ sohResistance }}%</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-label">电池温度</div>
          <div class="stat-value temp-value">{{ latest.temperature ?? '--' }} <span class="stat-unit">°C</span></div>
          <div class="stat-sub">环境 {{ latest.ambientTemp ?? '--' }} °C</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-label">电压不均衡度</div>
          <div class="stat-value imbalance-value">{{ voltageImbalanceMv }} <span class="stat-unit">mV</span></div>
          <div class="stat-sub">{{ latest.numCells ?? '--' }} 串单体</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表行 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="chart-card" shadow="hover">
          <template #header><span>SOC 仪表盘</span></template>
          <div ref="socGaugeRef" class="chart-container gauge-chart"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="10">
        <el-card class="chart-card" shadow="hover">
          <template #header><span>电压 / 电流 / SOC 趋势</span></template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="chart-card" shadow="hover">
          <template #header><span>温度趋势</span></template>
          <div ref="tempChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 单体电压柱状图 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="24">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span>单体电压分布 (13S)</span>
              <span style="font-size:12px;color:#909399;">
                最低: {{ latest.minCellVoltage ?? '--' }}V | 最高: {{ latest.maxCellVoltage ?? '--' }}V | 压差: {{ voltageImbalanceMv }}mV
              </span>
            </div>
          </template>
          <div ref="cellChartRef" class="chart-container cell-chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 单体SOC柱状图 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="24">
        <el-card class="chart-card" shadow="hover">
          <template #header><span>单体 SOC 分布</span></template>
          <div ref="cellSocChartRef" class="chart-container cell-chart"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getLatest } from '@/api/bms/realtime'

const latest = reactive({
  id: null, simTime: null, packVoltage: null, current: null, power: null,
  soc: null, soh: null, minCellVoltage: null, maxCellVoltage: null,
  voltageImbalance: null, temperature: null, ambientTemp: null, status: null,
  cellVoltage: [], cellSoc: [], capacityAh: null, cycleCount: null, numCells: null
})

// BMS状态（从bms_status JSON解析）
const bmsData = reactive({
  bms_status: 'normal',
  protection: { fault_status: 'normal', active_protections: [], warnings: [], alarms: [], charge_allowed: true, discharge_allowed: true },
  balancing: { active: false, cells: [] },
  soc: { ekf: 0, coulomb: 0, ocv: 0 },
  soh: { combined: 100, capacity: 100, resistance: 100, health_status: 'good' }
})

const history = reactive({ times: [], voltages: [], currents: [], socs: [], temps: [] })
const MAX_HISTORY = 60
const lastUpdateTime = ref('--')
let refreshTimer = null

const socGaugeRef = ref(null)
const trendChartRef = ref(null)
const tempChartRef = ref(null)
const cellChartRef = ref(null)
const cellSocChartRef = ref(null)
let socGaugeChart = null, trendChart = null, tempChart = null, cellChart = null, cellSocChart = null

// 计算属性
const statusText = computed(() => {
  const s = latest.status
  if (s === 'discharging') return '放电中'
  if (s === 'charging') return '充电中'
  if (s === 'resting') return '静置'
  if (s === 'error') return '故障'
  return s || '未知'
})
const statusTagType = computed(() => {
  const s = latest.status
  if (s === 'discharging') return 'warning'
  if (s === 'charging') return 'success'
  if (s === 'error') return 'danger'
  return 'info'
})
const currentClass = computed(() => {
  if (latest.current > 0) return 'discharge-color'
  if (latest.current < 0) return 'charge-color'
  return ''
})
const voltageImbalanceMv = computed(() => {
  if (latest.voltageImbalance == null) return '--'
  return (latest.voltageImbalance * 1000).toFixed(1)
})

// BMS状态计算属性
const bmsStatusText = computed(() => {
  const s = bmsData.bms_status
  return { normal: '正常', warning: '预警', alarm: '告警', fault: '故障' }[s] || s
})
const bmsStatusType = computed(() => {
  return { normal: 'success', warning: 'warning', alarm: 'danger', fault: 'danger' }[bmsData.bms_status] || 'info'
})
const protectionText = computed(() => {
  return { normal: '正常', warning: '预警', alarm: '告警', fault: '保护动作' }[bmsData.protection.fault_status] || '正常'
})
const protectionType = computed(() => {
  return { normal: 'success', warning: 'warning', alarm: 'danger', fault: 'danger' }[bmsData.protection.fault_status] || 'info'
})
const balancingActive = computed(() => bmsData.balancing.active)
const activeAlarms = computed(() => bmsData.protection.alarms || [])
const activeWarnings = computed(() => bmsData.protection.warnings || [])
const socCoulomb = computed(() => (bmsData.soc.coulomb * 100).toFixed(1))
const socOcv = computed(() => (bmsData.soc.ocv * 100).toFixed(1))
const sohCapacity = computed(() => bmsData.soh.capacity.toFixed(1))
const sohResistance = computed(() => bmsData.soh.resistance.toFixed(1))

// 图表初始化
function initCharts() {
  if (socGaugeRef.value) { socGaugeChart = echarts.init(socGaugeRef.value); updateSocGauge() }
  if (trendChartRef.value) { trendChart = echarts.init(trendChartRef.value); updateTrendChart() }
  if (tempChartRef.value) { tempChart = echarts.init(tempChartRef.value); updateTempChart() }
  if (cellChartRef.value) { cellChart = echarts.init(cellChartRef.value); updateCellChart() }
  if (cellSocChartRef.value) { cellSocChart = echarts.init(cellSocChartRef.value); updateCellSocChart() }
}

function updateSocGauge() {
  if (!socGaugeChart) return
  const soc = latest.soc ?? 0
  socGaugeChart.setOption({
    series: [{
      type: 'gauge', startAngle: 200, endAngle: -20, min: 0, max: 100,
      progress: { show: true, width: 18 },
      axisLine: { lineStyle: { width: 18, color: [[0.2, '#ee6666'], [0.5, '#fac858'], [1, '#5470c6']] } },
      pointer: { width: 5 },
      axisTick: { distance: -24, length: 6, lineStyle: { color: '#fff', width: 1 } },
      splitLine: { distance: -28, length: 10, lineStyle: { color: '#fff', width: 2 } },
      axisLabel: { color: '#999', distance: 35, fontSize: 11 },
      anchor: { show: true, size: 14, itemStyle: { color: '#5470c6' } },
      title: { offsetCenter: [0, '70%'], fontSize: 14, color: '#999' },
      detail: { valueAnimation: true, fontSize: 32, offsetCenter: [0, '35%'], formatter: '{value}%', color: soc < 20 ? '#ee6666' : soc < 50 ? '#fac858' : '#5470c6' },
      data: [{ value: soc.toFixed(1), name: 'SOC' }]
    }]
  })
}

function updateTrendChart() {
  if (!trendChart) return
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['电压(V)', '电流(A)', 'SOC(%)'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: history.times, axisLabel: { fontSize: 10 } },
    yAxis: [
      { type: 'value', name: 'V/A', position: 'left' },
      { type: 'value', name: 'SOC%', position: 'right', min: 80, max: 100 }
    ],
    series: [
      { name: '电压(V)', type: 'line', smooth: true, data: history.voltages, itemStyle: { color: '#5470c6' }, lineStyle: { width: 2 } },
      { name: '电流(A)', type: 'line', smooth: true, data: history.currents, itemStyle: { color: '#ee6666' }, lineStyle: { width: 2 } },
      { name: 'SOC(%)', type: 'line', smooth: true, yAxisIndex: 1, data: history.socs, itemStyle: { color: '#91cc75' }, lineStyle: { width: 2 } }
    ]
  })
}

function updateTempChart() {
  if (!tempChart) return
  tempChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['电池温度(°C)', '环境温度(°C)'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: history.times, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', name: '°C' },
    series: [
      { name: '电池温度(°C)', type: 'line', smooth: true, data: history.temps, itemStyle: { color: '#ee6666' }, areaStyle: { opacity: 0.1 } },
      { name: '环境温度(°C)', type: 'line', smooth: true, data: history.temps.map(() => latest.ambientTemp ?? 25), itemStyle: { color: '#5470c6' }, lineStyle: { type: 'dashed' } }
    ]
  })
}

function updateCellChart() {
  if (!cellChart || !latest.cellVoltage?.length) return
  const labels = latest.cellVoltage.map((_, i) => `C${i + 1}`)
  cellChart.setOption({
    tooltip: { trigger: 'axis', formatter: (params) => `${params[0].name}: ${params[0].value}V` },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: 'V', min: 3.8, max: 4.2 },
    series: [{
      type: 'bar',
      data: latest.cellVoltage.map(v => ({ value: v, itemStyle: { color: v < 3.9 ? '#ee6666' : v > 4.1 ? '#fac858' : '#5470c6' } })),
      barWidth: '50%',
      label: { show: true, position: 'top', fontSize: 10, formatter: (p) => p.value.toFixed(3) }
    }]
  })
}

function updateCellSocChart() {
  if (!cellSocChart || !latest.cellSoc?.length) return
  const labels = latest.cellSoc.map((_, i) => `C${i + 1}`)
  cellSocChart.setOption({
    tooltip: { trigger: 'axis', formatter: (params) => `${params[0].name}: ${params[0].value}%` },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '%', min: 85, max: 95 },
    series: [{
      type: 'bar',
      data: latest.cellSoc.map(v => ({ value: v, itemStyle: { color: v < 88 ? '#ee6666' : v > 92 ? '#91cc75' : '#fac858' } })),
      barWidth: '50%',
      label: { show: true, position: 'top', fontSize: 10, formatter: (p) => p.value.toFixed(1) }
    }]
  })
}

// 拉取数据
async function fetchData() {
  try {
    const res = await getLatest()
    if (res.code === 200 && res.data) {
      const d = res.data
      Object.assign(latest, d)
      if (typeof d.cellVoltage === 'string') { try { latest.cellVoltage = JSON.parse(d.cellVoltage) } catch { latest.cellVoltage = [] } }
      if (typeof d.cellSoc === 'string') { try { latest.cellSoc = JSON.parse(d.cellSoc) } catch { latest.cellSoc = [] } }

      // 解析BMS状态JSON
      if (d.bms_status && typeof d.bms_status === 'string') {
        try {
          const bms = JSON.parse(d.bms_status)
          bmsData.bms_status = bms.bms_status || 'normal'
          if (bms.protection) Object.assign(bmsData.protection, bms.protection)
          if (bms.balancing) Object.assign(bmsData.balancing, bms.balancing)
          if (bms.soc) Object.assign(bmsData.soc, bms.soc)
          if (bms.soh) Object.assign(bmsData.soh, bms.soh)
        } catch (e) { console.warn('BMS status parse error:', e) }
      }

      // 更新历史
      const timeLabel = d.simTime != null ? `${d.simTime}s` : new Date().toLocaleTimeString()
      history.times.push(timeLabel)
      history.voltages.push(d.packVoltage)
      history.currents.push(d.current)
      history.socs.push(d.soc)
      history.temps.push(d.temperature)
      if (history.times.length > MAX_HISTORY) {
        history.times.shift(); history.voltages.shift(); history.currents.shift(); history.socs.shift(); history.temps.shift()
      }
      lastUpdateTime.value = new Date().toLocaleTimeString()

      updateSocGauge(); updateTrendChart(); updateTempChart(); updateCellChart(); updateCellSocChart()
    }
  } catch (e) { console.error('获取电池数据失败:', e) }
}

function handleResize() {
  socGaugeChart?.resize(); trendChart?.resize(); tempChart?.resize(); cellChart?.resize(); cellSocChart?.resize()
}

onMounted(async () => {
  await nextTick()
  initCharts()
  await fetchData()
  refreshTimer = setInterval(fetchData, 2000)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  window.removeEventListener('resize', handleResize)
  socGaugeChart?.dispose(); trendChart?.dispose(); tempChart?.dispose(); cellChart?.dispose(); cellSocChart?.dispose()
})
</script>

<style scoped>
.bms-dashboard { padding: 16px; background: #f0f2f5; min-height: 100vh; }
.dashboard-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; padding: 0 8px; flex-wrap: wrap; gap: 12px; }
.header-left h1 { margin: 0 0 8px 0; font-size: 22px; color: #303133; }
.header-badges { display: flex; gap: 8px; flex-wrap: wrap; }
.header-info { display: flex; align-items: center; gap: 16px; }
.update-time { font-size: 13px; color: #909399; }
.alert-banner { margin-bottom: 12px; }
.stat-cards { margin-bottom: 16px; }
.stat-card { margin-bottom: 12px; border-radius: 8px; }
.stat-label { font-size: 13px; color: #909399; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: 700; color: #303133; line-height: 1.2; }
.stat-unit { font-size: 14px; font-weight: 400; color: #909399; }
.stat-sub { font-size: 12px; color: #c0c4cc; margin-top: 6px; }
.soc-compare { color: #67c23a; }
.soc-value { color: #5470c6; }
.soh-value { color: #91cc75; }
.temp-value { color: #ee6666; }
.imbalance-value { color: #fac858; }
.discharge-color { color: #ee6666; }
.charge-color { color: #67c23a; }
.chart-row { margin-bottom: 16px; }
.chart-card { border-radius: 8px; margin-bottom: 12px; }
.chart-container { height: 280px; width: 100%; }
.gauge-chart { height: 260px; }
.cell-chart { height: 260px; }
</style>
