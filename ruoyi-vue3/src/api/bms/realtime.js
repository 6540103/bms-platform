import request from '@/utils/request'

// 查询电池实时数据列表
export function listRealtime(query) {
  return request({
    url: '/bms/realtime/list',
    method: 'get',
    params: query,
    headers: { isToken: false }
  })
}

// 获取最新一条电池数据
export function getLatest() {
  return request({
    url: '/bms/realtime/latest',
    method: 'get',
    headers: { isToken: false }
  })
}

// 获取电池实时数据详细
export function getRealtime(id) {
  return request({
    url: '/bms/realtime/' + id,
    method: 'get'
  })
}
