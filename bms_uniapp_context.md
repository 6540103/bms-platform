# BMS 电池管理系统 - uni-app 移动端开发上下文同步文档

> 本文档用于在 Windows 11 虚拟机的豆包工作中同步项目上下文，以便开展 uni-app 移动端开发。

---

## 一、项目概述

### 1.1 项目目标
开发一套**电池管理系统（BMS）软件仿真平台**，参考九号电动类电动车锂电池（48V 13S 三元锂），先做软件仿真/算法验证，后续可扩展到硬件。

### 1.2 当前进度
| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 | Python 电池仿真 + Kafka 消息队列 | ✅ 完成 |
| Phase 2 | Java Spring Boot + RuoYi 后端 | ✅ 完成 |
| Phase 3 | Vue 3 + Element Plus + ECharts Web 前端 | ✅ 完成 |
| Phase 4 | BMS 核心算法（SOC EKF/保护/均衡/SOH） | ✅ 完成 |
| Phase 5 | **uni-app 移动端** | 🔄 当前任务 |

### 1.3 技术栈
- **仿真引擎**：Python 3 + Thevenin 一阶等效电路模型 + BMS 算法
- **消息队列**：Kafka 3.8.0（KRaft 模式）
- **后端**：Java 17 + Spring Boot 4.1.0 + RuoYi-Vue 3.9.2 + MyBatis + MySQL 8.0 + Redis 7
- **Web 前端**：Vue 3 + Element Plus + ECharts 5 + Vite 6
- **移动端**：**uni-app（Vue 3 语法）+ uView UI**（待开发）
- **通信**：Python → Kafka → Java 后端 → REST API → 前端/移动端

---

## 二、运行环境与访问地址

### 2.1 服务器
所有后端服务运行在 **Ubuntu 26 虚拟机**上：
- IP：`192.168.1.26`
- SSH 用户：`kevin`，密码：`luo800607`

### 2.2 服务端口
| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 API | `http://192.168.1.26:8080` | Spring Boot + RuoYi |
| Web 前端 | `http://192.168.1.26:8081/bms/dashboard` | Vue 3 仪表盘 |
| Kafka | `192.168.1.26:9092` | 消息队列 |
| MySQL | `192.168.1.26:3306` | root/root123，数据库名 `ry` |
| Redis | `192.168.1.26:6379` | 无密码 |

### 2.3 启动方式
Ubuntu 桌面上有一键启动脚本：
- `BMS启动.desktop`：双击启动全部服务
- `BMS停止.desktop`：双击停止全部服务
- 脚本路径：`~/Desktop/start_bms.sh` / `~/Desktop/stop_bms.sh`

---

## 三、后端 API 接口文档

### 3.1 认证说明
BMS 相关接口（`/bms/**`）已加入 RuoYi 匿名访问白名单，**不需要登录 Token**，可直接调用。

### 3.2 核心接口

#### （1）获取最新一条电池实时数据
- **URL**：`GET http://192.168.1.26:8080/bms/realtime/latest`
- **请求参数**：无
- **响应示例**：
```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "id": 1090,
    "simTime": 436.0,
    "packVoltage": 51.86,
    "current": 20.0,
    "power": 1037.2,
    "soc": 84.08,
    "soh": 100.0,
    "minCellVoltage": 3.98,
    "maxCellVoltage": 4.00,
    "voltageImbalance": 0.02,
    "temperature": 26.5,
    "ambientTemp": 25.0,
    "status": "discharging",
    "cellVoltage": "[4.00, 3.99, 3.98, ...]",
    "cellSoc": "[84.1, 84.0, 83.9, ...]",
    "capacityAh": 40.0,
    "cycleCount": 0,
    "numCells": 13,
    "bmsStatus": "{...BMS完整状态JSON...}",
    "createTime": "2026-09-10 08:00:00"
  }
}
```

#### （2）查询电池实时数据列表（分页）
- **URL**：`GET http://192.168.1.26:8080/bms/realtime/list`
- **请求参数**：`pageNum`（页码）、`pageSize`（每页条数）、`status`（可选，按状态筛选）
- **响应**：RuoYi 标准分页格式 `{ code: 200, rows: [...], total: 100 }`

#### （3）获取单条详情
- **URL**：`GET http://192.168.1.26:8080/bms/realtime/{id}`

#### （4）导出数据
- **URL**：`GET http://192.168.1.26:8080/bms/realtime/export`

### 3.3 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| simTime | float | 仿真时间（秒） |
| packVoltage | float | 电池组总电压（V），13S 约 48-54V |
| current | float | 电流（A），正=放电，负=充电 |
| power | float | 功率（W） |
| soc | float | 荷电状态（%），EKF 估算值 |
| soh | float | 健康状态（%） |
| minCellVoltage | float | 最低单体电压（V） |
| maxCellVoltage | float | 最高单体电压（V） |
| voltageImbalance | float | 电压不均衡度（V），= max - min |
| temperature | float | 电池温度（°C） |
| ambientTemp | float | 环境温度（°C） |
| status | string | 状态：discharging（放电）/ charging（充电）/ resting（静置）/ error（故障） |
| cellVoltage | string | 13个单体电压数组的 JSON 字符串 |
| cellSoc | string | 13个单体 SOC 数组的 JSON 字符串 |
| capacityAh | float | 电池容量（Ah），默认 40Ah |
| cycleCount | int | 循环次数 |
| numCells | int | 串联单体数，固定 13 |
| bmsStatus | string | BMS 完整状态 JSON 字符串（见下文） |

### 3.4 bmsStatus 字段详解（JSON 字符串，需 JSON.parse）

```json
{
  "bms_status": "normal",        // normal/warning/alarm/fault
  "total_runtime_s": 436,
  "protection_event_count": 0,
  "balance_event_count": 0,
  "soc": {
    "ekf": 0.8408,               // EKF 估算 SOC（0-1）
    "coulomb": 0.8395,           // 库仑计数 SOC
    "ocv": 0.85                   // OCV 查表 SOC
  },
  "protection": {
    "fault_status": "normal",     // normal/warning/alarm/fault
    "active_protections": [],     // 触发的保护列表
    "warnings": [],                // 预警列表
    "alarms": [],                  // 告警列表
    "charge_allowed": true,
    "discharge_allowed": true
  },
  "balancing": {
    "active": false,               // 是否正在均衡
    "cells": []                    // 正在均衡的电芯编号
  },
  "soh": {
    "combined": 99.99,
    "capacity": 99.99,
    "resistance": 100.0,
    "health_status": "good"
  }
}
```

### 3.5 保护类型说明
`active_protections` / `warnings` / `alarms` 中可能出现的保护类型：
- `overvoltage`：过压（单体 > 4.15/4.18/4.20V）
- `undervoltage`：欠压（单体 < 3.20/3.10/3.00V）
- `discharge_overcurrent`：放电过流（> 80/100/120A）
- `charge_overcurrent`：充电过流（< -40/-50/-60A）
- `short_circuit`：短路（> 200A）
- `overtemperature`：过温（> 45/55/60°C）
- `low_temperature`：低温（< 10/5/0°C，0°C 以下禁止充电）
- `low_soc`：SOC 过低
- `cell_imbalance`：单体不均衡

---

## 四、数据库表结构

### 表名：`ry.bms_realtime_data`
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint PK | 自增主键 |
| sim_time | double | 仿真时间（秒） |
| pack_voltage | double | 总电压（V） |
| current | double | 电流（A） |
| power | double | 功率（W） |
| soc | double | SOC（%） |
| soh | double | SOH（%） |
| min_cell_voltage | double | 最低单体电压 |
| max_cell_voltage | double | 最高单体电压 |
| voltage_imbalance | double | 电压不均衡度 |
| temperature | double | 电池温度 |
| ambient_temp | double | 环境温度 |
| status | varchar(20) | 状态 |
| cell_voltage | text | 单体电压 JSON |
| cell_soc | text | 单体 SOC JSON |
| capacity_ah | double | 容量（Ah） |
| cycle_count | int | 循环次数 |
| num_cells | int | 单体数 |
| bms_status | json | BMS 完整状态 JSON |
| create_time | datetime | 创建时间 |

**数据频率**：Python 仿真 1Hz 推送 Kafka，后端每 10 条存 1 条到数据库（约每 10 秒 1 条）。

---

## 五、现有 Web 端功能（参考）

Web 前端仪表盘（`http://192.168.1.26:8081/bms/dashboard`）已实现：
1. **顶部状态徽章**：BMS 状态、保护状态、均衡状态（颜色编码）
2. **告警横幅**：有告警时红色横幅，有预警时黄色横幅
3. **6 张状态卡片**：总电压、电流、SOC（EKF+库仑+OCV 对比）、SOH（容量+内阻细分）、温度、电压不均衡度
4. **SOC 仪表盘**：ECharts 仪表盘
5. **趋势图**：电压/电流/SOC 三轴折线图、温度趋势图
6. **单体电压柱状图**：13 个单体电压，颜色编码（过低红色/过高黄色/正常蓝色）
7. **单体 SOC 柱状图**：13 个单体 SOC

页面每 2 秒自动刷新一次。

---

## 六、uni-app 移动端开发需求

### 6.1 技术选型
- **框架**：uni-app（Vue 3 语法，`<script setup>`）
- **UI 组件库**：uView UI（uview-plus，支持 Vue 3）
- **图表**：ucharts（uni-app 生态图表库，跨平台兼容好）或 uCharts
- **HTTP 请求**：uni.request 封装
- **目标平台**：先做 H5 验证，后续编译到微信小程序/App

### 6.2 页面规划（第一期）

#### 页面 1：实时监控仪表盘（首页）
- 顶部：BMS 状态徽章（正常/预警/告警/故障，颜色编码）+ 电池状态（放电/充电/静置）
- 核心数据卡片（2列网格）：
  - SOC（大字号，EKF 值）+ 小字显示库仑/OCV 对比
  - 总电压（V）
  - 电流（A）+ 功率（W）
  - SOH（%）
  - 电池温度（°C）+ 环境温度
  - 电压不均衡度（mV）
- 告警横幅：有告警/预警时显示
- SOC 仪表盘（ucharts 仪表盘组件）
- 电压/电流/SOC 趋势图（ucharts 折线图，显示最近 30-60 条数据）
- 自动刷新：每 2-3 秒调用一次 latest 接口

#### 页面 2：电池详情
- 13 个单体电压列表（可滚动，显示每个电芯编号、电压、SOC）
- 最低/最高单体电压高亮
- 电压不均衡度显示
- 单体电压柱状图（ucharts）

#### 页面 3：历史数据
- 时间范围选择（最近1小时/今天/最近7天）
- 历史趋势图（电压/电流/SOC/温度）
- 数据列表（分页加载）

#### 页面 4：告警记录
- 告警/预警列表（时间、类型、级别、描述）
- 按级别筛选（全部/告警/预警）

#### 页面 5：设置
- 自动刷新间隔设置（2s/5s/10s/手动）
- 后端 API 地址配置
- 关于页面

### 6.3 底部 TabBar
- 首页（实时监控）
- 电池详情
- 历史数据
- 告警
- 我的/设置

### 6.4 开发要点
1. **API 封装**：封装 `request.js`，baseURL 指向 `http://192.168.1.26:8080`，BMS 接口不需要 token
2. **数据解析**：`cellVoltage`、`cellSoc`、`bmsStatus` 字段是 JSON 字符串，需要 `JSON.parse()`
3. **实时刷新**：用 `setInterval` 定时调用 latest 接口，页面销毁时清除定时器
4. **图表选型**：ucharts 对 uni-app 跨平台兼容最好，推荐使用 `qiun-data-charts` 组件
5. **响应式**：适配不同手机屏幕尺寸，使用 rpx 单位
6. **H5 调试**：先运行到 H5，在浏览器中调试，确认功能后再编译到小程序/App

---

## 七、项目文件路径（Ubuntu VM 上）

| 内容 | 路径 |
|------|------|
| 项目根目录 | `/home/kevin/bms-platform/` |
| Python 仿真 | `/home/kevin/bms-platform/simulation/` |
| BMS 算法包 | `/home/kevin/bms-platform/simulation/bms_algorithms/` |
| Java 后端 | `/home/kevin/bms-platform/ruoyi-backend/` |
| BMS 后端模块 | `ruoyi-system/.../domain/BmsRealtimeData.java` 等 |
| Kafka 消费者 | `ruoyi-admin/.../kafka/BmsKafkaConsumer.java` |
| BMS Controller | `ruoyi-admin/.../controller/bms/BmsRealtimeDataController.java` |
| Vue 3 前端 | `/home/kevin/bms-platform/ruoyi-vue3/` |
| Web 仪表盘 | `ruoyi-vue3/src/views/bms/dashboard/index.vue` |
| BMS API 模块 | `ruoyi-vue3/src/api/bms/realtime.js` |
| Docker 编排 | `/home/kevin/bms-platform/docker-compose.yml` |
| 启动脚本 | `/home/kevin/Desktop/start_bms.sh` / `stop_bms.sh` |

---

## 八、电池参数参考

| 参数 | 值 |
|------|-----|
| 电池类型 | 三元锂（NMC） |
| 拓扑 | 13S1P（13串1并） |
| 标称电压 | 48V（13 × 3.7V） |
| 满电电压 | 54.6V（13 × 4.2V） |
| 截止电压 | 39.0V（13 × 3.0V） |
| 容量 | 40Ah（可选 30/60Ah） |
| 单体 OCV 范围 | 3.0V ~ 4.2V |
| 内阻 R0 | ~3mΩ |
| 电流约定 | 正=放电，负=充电 |
| 默认工况 | 20A 恒流放电 |

---

## 九、注意事项

1. **后端服务必须先启动**：uni-app 调用 API 前，确保 Ubuntu VM 上的 BMS 服务已启动（运行桌面启动脚本）
2. **跨域问题**：H5 调试时可能遇到跨域，uni-app 的 manifest.json 中可配置 devServer 代理，或后端已配置 CORS
3. **数据频率**：latest 接口返回的是数据库中最新一条（约每 10 秒更新），不是实时 1Hz 数据；如需更高频率，可后续扩展 WebSocket
4. **bmsStatus 可能为 null**：早期数据可能没有 bmsStatus 字段，前端需做判空处理
5. **cellVoltage/cellSoc 是字符串**：从 API 返回的是 JSON 字符串，必须 `JSON.parse()` 后才能使用
6. **第一期先做 H5**：建议先运行到 H5 平台调试，功能验证通过后再考虑编译到微信小程序或 App

---

## 十、开发任务清单

- [ ] 创建 uni-app 项目（Vue 3 + uView UI + ucharts）
- [ ] 封装 HTTP 请求模块（request.js）
- [ ] 封装 BMS API 模块（realtime.js）
- [ ] 实现底部 TabBar 导航
- [ ] 页面1：实时监控仪表盘（核心数据卡片 + SOC仪表盘 + 趋势图 + 自动刷新）
- [ ] 页面2：电池详情（单体电压列表 + 柱状图）
- [ ] 页面3：历史数据（趋势图 + 数据列表）
- [ ] 页面4：告警记录
- [ ] 页面5：设置（刷新间隔 + API地址 + 关于）
- [ ] H5 平台调试验证
- [ ] （可选）编译到微信小程序
- [ ] （可选）云打包成 Android App

---

*文档版本：v1.0 | 更新时间：2026-09-10*
