<template>
  <view class="alarm-page">
    <!-- 统计卡片 -->
    <view class="card">
      <view class="card-title">告警统计</view>
      <view class="alarm-stats">
        <view class="stat-item alarm">
          <text class="stat-count">{{ alarmCount }}</text>
          <text class="stat-label">告警</text>
        </view>
        <view class="stat-item warning">
          <text class="stat-count">{{ warningCount }}</text>
          <text class="stat-label">预警</text>
        </view>
        <view class="stat-item normal">
          <text class="stat-count">{{ normalCount }}</text>
          <text class="stat-label">正常</text>
        </view>
      </view>
    </view>

    <!-- 筛选 -->
    <view class="card">
      <view class="card-title">筛选</view>
      <view class="filter-tabs">
        <view v-for="tab in filterTabs" :key="tab.value" class="filter-tab" :class="{ active: currentFilter === tab.value }" @click="currentFilter = tab.value">
          {{ tab.label }}
        </view>
      </view>
    </view>

    <!-- 告警列表 -->
    <view class="card">
      <view class="card-title">告警记录</view>
      <view class="alarm-list">
        <view v-for="item in filteredList" :key="item.id" class="alarm-item" :class="item.level">
          <view class="alarm-icon">
            <text v-if="item.level === 'alarm'">⚠</text>
            <text v-else-if="item.level === 'warning'">⚡</text>
            <text v-else>✓</text>
          </view>
          <view class="alarm-content">
            <view class="alarm-header">
              <text class="alarm-type">{{ item.type }}</text>
              <text class="alarm-time">{{ item.time }}</text>
            </view>
            <view class="alarm-desc">{{ item.description }}</view>
            <view class="alarm-detail" v-if="item.detail">
              <text>{{ item.detail }}</text>
            </view>
          </view>
          <view class="alarm-level-badge" :class="item.level">
            {{ item.levelText }}
          </view>
        </view>
      </view>
      <view v-if="filteredList.length === 0" class="empty-text">
        <text class="empty-icon">✓</text>
        <text>暂无{{ currentFilter === 'all' ? '' : currentFilter === 'alarm' ? '告警' : '预警' }}记录</text>
      </view>
    </view>

    <!-- 保护类型说明 -->
    <view class="card">
      <view class="card-title">保护类型说明</view>
      <view class="protection-list">
        <view v-for="p in protectionTypes" :key="p.key" class="protection-item">
          <view class="protection-name">{{ p.name }}</view>
          <view class="protection-desc">{{ p.desc }}</view>
          <view class="protection-thresholds">
            <text class="threshold warning">预警: {{ p.warning }}</text>
            <text class="threshold alarm">告警: {{ p.alarm }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getLatestData, parseBmsStatus } from '@/api/bms.js'

const filterTabs = [
  { label: '全部', value: 'all' },
  { label: '告警', value: 'alarm' },
  { label: '预警', value: 'warning' }
]

const protectionTypes = [
  { key: 'overvoltage', name: '过压保护', desc: '单体电压超过阈值', warning: '>4.15V', alarm: '>4.20V' },
  { key: 'undervoltage', name: '欠压保护', desc: '单体电压低于阈值', warning: '<3.20V', alarm: '<3.00V' },
  { key: 'discharge_overcurrent', name: '放电过流', desc: '放电电流超过阈值', warning: '>80A', alarm: '>120A' },
  { key: 'charge_overcurrent', name: '充电过流', desc: '充电电流超过阈值', warning: '<-40A', alarm: '<-60A' },
  { key: 'overtemperature', name: '过温保护', desc: '电池温度过高', warning: '>45°C', alarm: '>60°C' },
  { key: 'low_temperature', name: '低温保护', desc: '电池温度过低', warning: '<10°C', alarm: '<0°C' },
  { key: 'cell_imbalance', name: '单体不均衡', desc: '单体电压差过大', warning: '>50mV', alarm: '>100mV' },
  { key: 'low_soc', name: 'SOC过低', desc: '剩余电量过低', warning: '<20%', alarm: '<5%' }
]

const currentFilter = ref('all')
const alarmList = ref([])
const latestData = ref({})

const alarmCount = computed(() => alarmList.value.filter(a => a.level === 'alarm').length)
const warningCount = computed(() => alarmList.value.filter(a => a.level === 'warning').length)
const normalCount = computed(() => alarmList.value.filter(a => a.level === 'normal').length)

const filteredList = computed(() => {
  if (currentFilter.value === 'all') return alarmList.value
  return alarmList.value.filter(a => a.level === currentFilter.value)
})

async function fetchData() {
  try {
    const res = await getLatestData()
    if (res.code === 200 && res.data) {
      latestData.value = res.data
      parseAlarms(res.data)
    }
  } catch (e) {
    console.error(e)
  }
}

function parseAlarms(data) {
  const bmsStatus = parseBmsStatus(data.bmsStatus)
  const list = []

  if (bmsStatus) {
    const protection = bmsStatus.protection || {}

    // 告警
    ;(protection.alarms || []).forEach(a => {
      list.push({
        id: `alarm-${a}-${Date.now()}`,
        level: 'alarm',
        levelText: '告警',
        type: getProtectionName(a),
        description: getProtectionDesc(a),
        detail: `触发时间: ${data.createTime || '--'}`,
        time: data.createTime?.slice(5, 16) || '--'
      })
    })

    // 预警
    ;(protection.warnings || []).forEach(w => {
      list.push({
        id: `warning-${w}-${Date.now()}`,
        level: 'warning',
        levelText: '预警',
        type: getProtectionName(w),
        description: getProtectionDesc(w),
        detail: `触发时间: ${data.createTime || '--'}`,
        time: data.createTime?.slice(5, 16) || '--'
      })
    })
  }

  // 如果没有告警，显示正常状态
  if (list.length === 0) {
    list.push({
      id: 'normal-1',
      level: 'normal',
      levelText: '正常',
      type: '系统正常',
      description: '当前无告警和预警',
      detail: `BMS状态: ${bmsStatus?.bms_status || 'normal'}`,
      time: data.createTime?.slice(5, 16) || '--'
    })
  }

  alarmList.value = list
}

function getProtectionName(key) {
  const map = {
    overvoltage: '过压保护',
    undervoltage: '欠压保护',
    discharge_overcurrent: '放电过流',
    charge_overcurrent: '充电过流',
    short_circuit: '短路保护',
    overtemperature: '过温保护',
    low_temperature: '低温保护',
    low_soc: 'SOC过低',
    cell_imbalance: '单体不均衡'
  }
  return map[key] || key
}

function getProtectionDesc(key) {
  const map = {
    overvoltage: '单体电压超过安全阈值',
    undervoltage: '单体电压低于安全阈值',
    discharge_overcurrent: '放电电流超过额定值',
    charge_overcurrent: '充电电流超过额定值',
    short_circuit: '检测到短路故障',
    overtemperature: '电池温度过高',
    low_temperature: '电池温度过低',
    low_soc: '剩余电量过低',
    cell_imbalance: '单体电压差异过大'
  }
  return map[key] || key
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.alarm-page { padding-bottom: 40rpx; }
.alarm-stats { display: flex; gap: 16rpx; }
.stat-item { flex: 1; text-align: center; padding: 24rpx; border-radius: 16rpx; }
.stat-item.alarm { background: rgba(255, 82, 82, 0.1); border: 1rpx solid rgba(255, 82, 82, 0.3); }
.stat-item.warning { background: rgba(255, 171, 0, 0.1); border: 1rpx solid rgba(255, 171, 0, 0.3); }
.stat-item.normal { background: rgba(0, 200, 83, 0.1); border: 1rpx solid rgba(0, 200, 83, 0.3); }
.stat-count { display: block; font-size: 48rpx; font-weight: 700; }
.alarm .stat-count { color: #ff5252; }
.warning .stat-count { color: #ffab00; }
.normal .stat-count { color: #00c853; }
.stat-label { font-size: 24rpx; color: #8b8b9e; }
.filter-tabs { display: flex; gap: 12rpx; }
.filter-tab {
  flex: 1; text-align: center; padding: 16rpx; border-radius: 12rpx;
  font-size: 24rpx; color: #8b8b9e; background: rgba(255, 255, 255, 0.03);
}
.filter-tab.active { background: rgba(0, 212, 255, 0.2); color: #00d4ff; border: 1rpx solid rgba(0, 212, 255, 0.3); }
.alarm-list { display: flex; flex-direction: column; gap: 12rpx; }
.alarm-item { display: flex; padding: 16rpx; background: rgba(255, 255, 255, 0.03); border-radius: 12rpx; border-left: 6rpx solid #9e9e9e; }
.alarm-item.alarm { border-left-color: #ff5252; background: rgba(255, 82, 82, 0.05); }
.alarm-item.warning { border-left-color: #ffab00; background: rgba(255, 171, 0, 0.05); }
.alarm-item.normal { border-left-color: #00c853; background: rgba(0, 200, 83, 0.05); }
.alarm-icon { width: 48rpx; height: 48rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24rpx; margin-right: 16rpx; flex-shrink: 0; }
.alarm .alarm-icon { background: rgba(255, 82, 82, 0.2); color: #ff5252; }
.warning .alarm-icon { background: rgba(255, 171, 0, 0.2); color: #ffab00; }
.normal .alarm-icon { background: rgba(0, 200, 83, 0.2); color: #00c853; }
.alarm-content { flex: 1; }
.alarm-header { display: flex; justify-content: space-between; align-items: center; }
.alarm-type { font-size: 26rpx; font-weight: 600; color: #fff; }
.alarm-time { font-size: 20rpx; color: #8b8b9e; }
.alarm-desc { font-size: 22rpx; color: #b0b0b0; margin-top: 4rpx; }
.alarm-detail { font-size: 20rpx; color: #8b8b9e; margin-top: 4rpx; }
.alarm-level-badge { font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 8rpx; align-self: flex-start; flex-shrink: 0; }
.alarm .alarm-level-badge { background: rgba(255, 82, 82, 0.2); color: #ff5252; }
.warning .alarm-level-badge { background: rgba(255, 171, 0, 0.2); color: #ffab00; }
.normal .alarm-level-badge { background: rgba(0, 200, 83, 0.2); color: #00c853; }
.empty-text { text-align: center; padding: 48rpx; color: #8b8b9e; }
.empty-icon { display: block; font-size: 64rpx; color: #00c853; margin-bottom: 16rpx; }
.protection-list { display: flex; flex-direction: column; gap: 12rpx; }
.protection-item { padding: 16rpx; background: rgba(255, 255, 255, 0.03); border-radius: 12rpx; }
.protection-name { font-size: 26rpx; font-weight: 600; color: #00d4ff; }
.protection-desc { font-size: 22rpx; color: #b0b0b0; margin-top: 4rpx; }
.protection-thresholds { display: flex; gap: 24rpx; margin-top: 8rpx; }
.threshold { font-size: 20rpx; }
.threshold.warning { color: #ffab00; }
.threshold.alarm { color: #ff5252; }
</style>
