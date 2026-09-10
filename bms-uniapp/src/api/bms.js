// BMS 电池管理系统 API
import request from '@/utils/request.js'

// 获取最新一条实时数据
export function getLatestData() {
  return request({
    url: '/bms/realtime/latest',
    method: 'GET'
  })
}

// 获取实时数据列表（分页）
export function getDataList(params) {
  return request({
    url: '/bms/realtime/list',
    method: 'GET',
    data: params
  })
}

// 获取单条详情
export function getDataDetail(id) {
  return request({
    url: `/bms/realtime/${id}`,
    method: 'GET'
  })
}

// 解析 cellVoltage 字符串为数组
export function parseCellVoltage(str) {
  if (!str) return []
  try {
    return JSON.parse(str)
  } catch (e) {
    return []
  }
}

// 解析 cellSoc 字符串为数组
export function parseCellSoc(str) {
  if (!str) return []
  try {
    return JSON.parse(str)
  } catch (e) {
    return []
  }
}

// 解析 bmsStatus 字符串为对象
export function parseBmsStatus(str) {
  if (!str) return null
  try {
    return JSON.parse(str)
  } catch (e) {
    return null
  }
}

// 状态文本映射
export const statusMap = {
  discharging: { text: '放电中', color: '#ff9800' },
  charging: { text: '充电中', color: '#00c853' },
  resting: { text: '静置', color: '#9e9e9e' },
  error: { text: '故障', color: '#ff5252' }
}

// BMS 状态映射
export const bmsStatusMap = {
  normal: { text: '正常', class: 'status-normal' },
  warning: { text: '预警', class: 'status-warning' },
  alarm: { text: '告警', class: 'status-alarm' },
  fault: { text: '故障', class: 'status-fault' }
}
