# BMS 电池管理系统 - 移动端 (uni-app)

基于 uni-app (Vue 3 + Vite) 开发的 BMS 电池管理系统移动端应用，支持 H5、微信小程序等多平台。

## 快速访问

### 各服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **H5 移动端** | http://192.168.1.26:5173 | uni-app 编译的 H5 页面（开发模式） |
| **Web 管理端** | http://192.168.1.26:8081/bms/dashboard | Vue 前端管理页面 |
| **后端 API** | http://192.168.1.26:8080 | Spring Boot + RuoYi 后端接口 |
| **需求文档** | http://192.168.1.26:8081/bms_uniapp_context.md | 移动端需求说明文档 |
| **MySQL 数据库** | 192.168.1.26:3306 | 数据库名: ry |

### 手机访问

手机和电脑连接同一个 WiFi，在手机浏览器输入上述地址即可访问。

## 项目介绍

本项目是 BMS（Battery Management System，电池管理系统）的移动端应用，参考九号电动 48V 13S 三元锂电池参数开发。后端基于 RuoYi 框架（Spring Boot），已有 Web 管理端，本项目为移动端 uni-app 应用。

### 电池参数

- 电池类型：三元锂 13S1P
- 标称电压：48V
- 容量：40Ah
- 单体数量：13 个

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | uni-app | 3.0.0-alpha |
| 前端框架 | Vue | 3.4+ |
| 构建工具 | Vite | 5.2+ |
| UI 组件库 | uview-plus | 3.3+ |
| 样式 | SCSS | 1.77+ |
| 后端 | Spring Boot + RuoYi | - |
| 数据库 | MySQL | - |

## 项目结构

```
bms-uniapp/
├── index.html                  # H5 入口 HTML
├── package.json                # 依赖配置
├── vite.config.js              # Vite 配置（含 API 代理）
├── README.md                   # 项目说明文档
└── src/
    ├── main.js                 # 应用入口
    ├── App.vue                 # 根组件（全局样式）
    ├── manifest.json           # 应用配置（应用ID、名称、平台配置）
    ├── pages.json              # 页面路由 + TabBar 配置
    ├── uni.scss                # 全局 SCSS 变量
    ├── api/
    │   └── bms.js              # BMS API 封装 + 数据解析函数
    ├── utils/
    │   └── request.js          # HTTP 请求封装（uni.request）
    └── pages/
        ├── dashboard/          # 页面1：实时监控仪表盘
        │   └── index.vue
        ├── battery/            # 页面2：电池详情
        │   └── index.vue
        ├── history/            # 页面3：历史数据
        │   └── index.vue
        ├── alarm/              # 页面4：告警记录
        │   └── index.vue
        └── settings/           # 页面5：设置
            └── index.vue
```

## 页面功能说明

### 1. 实时监控 (dashboard)

- SOC 大卡片（EKF 估算，含库仑/OCV 对比）
- 6 格数据网格：总电压、电流、功率、SOH 健康度、电池温度、环境温度
- 13 单体电压柱状图（最低/最高/压差统计）
- 电压/电流/SOC 趋势数据
- BMS 状态详情：保护状态、均衡状态、充放电允许、循环次数、仿真时间
- 自动刷新（可配置间隔）

### 2. 电池详情 (battery)

- 电池概览：总电压、SOC、温度、压差
- 13 单体电压分布柱状图
- 单体详情列表：每个单体的电压、SOC、状态标记（正常/偏低/偏高）
- 极值统计：最低单体、最高单体高亮

### 3. 历史数据 (history)

- 时间范围筛选：最近1小时、今天、最近7天
- 数据趋势图：电压/电流/SOC/温度切换
- 分页数据列表：每条记录的时间、电压、电流、SOC、温度、状态
- 点击记录查看详情弹窗

### 4. 告警记录 (alarm)

- 告警统计：告警/预警/正常数量
- 筛选切换：全部/告警/预警
- 告警列表：告警类型、描述、时间、级别
- 8 种保护类型说明：过压、欠压、放电过流、充电过流、过温、低温、单体不均衡、SOC过低

### 5. 设置 (settings)

- 刷新间隔配置：2秒/5秒/10秒/30秒/手动
- 自动刷新开关
- API 地址配置与连接测试
- 清除缓存
- 关于信息（版本、技术栈、电池参数）

## API 接口说明

后端接口无需 Token（已加入 RuoYi 白名单），基础地址：`http://192.168.1.26:8080`

| 接口 | 方法 | 说明 |
|------|------|------|
| `/bms/realtime/latest` | GET | 获取最新实时数据 |
| `/bms/realtime/list` | GET | 分页获取历史数据列表 |
| `/bms/realtime/{id}` | GET | 获取单条数据详情 |

### 核心数据字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `packVoltage` | 电池组总电压 (V) | 52.77 |
| `current` | 电流 (A)，正值放电，负值充电 | 0.0 |
| `soc` | 剩余电量 (%) | 86.0 |
| `soh` | 健康度 (%) | 100.0 |
| `temperature` | 电池温度 (°C) | 25.0 |
| `cellVoltage` | 13单体电压，逗号分隔 | "4.067,4.055,..." |
| `cellSoc` | 13单体SOC，逗号分隔 | "86.7,85.5,..." |
| `bmsStatus` | BMS状态JSON（保护/均衡/充放电等） | - |
| `status` | 运行状态：discharging/charging/resting/error | resting |
| `cycleCount` | 循环次数 | 0 |

## 开发指南

### 环境要求

- Node.js >= 18
- npm >= 9

### 安装依赖

```bash
cd bms-uniapp
npm install
```

### H5 开发调试

```bash
npm run dev:h5
```

启动后访问：http://localhost:5173 或 http://192.168.1.26:5173

### 微信小程序开发调试

```bash
npm run dev:mp-weixin
```

使用微信开发者工具打开 `dist/dev/mp-weixin` 目录。

### 构建发布

```bash
# H5 生产构建
npm run build:h5

# 微信小程序生产构建
npm run build:mp-weixin
```

构建产物在 `dist/build/` 目录下。

### API 跨域处理

H5 开发模式下已在 `vite.config.js` 中配置代理：

```js
server: {
  proxy: {
    '/api': {
      target: 'http://192.168.1.26:8080',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

生产部署时需确保后端配置 CORS 或使用 Nginx 反向代理。

## 部署说明

### H5 部署

1. 执行 `npm run build:h5` 生成生产构建
2. 将 `dist/build/h5/` 目录部署到 Nginx 或其他静态文件服务器
3. 配置 Nginx 反向代理 `/api` 到后端服务

### 微信小程序部署

1. 执行 `npm run build:mp-weixin`
2. 使用微信开发者工具打开 `dist/build/mp-weixin`
3. 上传代码并提交审核

## 注意事项

1. **TabBar 图标**：当前使用默认图标，如需自定义图标，将 PNG 图标放入 `src/static/tabbar/` 目录，并在 `pages.json` 中配置路径
2. **开发模式**：当前运行的是开发模式（带 sourcemap、未压缩），性能和包体积不如生产模式
3. **自动刷新**：实时监控页面默认每 3 秒自动刷新，可在设置页面调整
4. **数据模拟**：趋势图部分使用模拟数据，实际使用时可对接历史数据接口

## 相关项目

- **后端项目**：RuoYi-Vue (Spring Boot)，端口 8080
- **Web 前端**：Vue 管理端，端口 8081
- **移动端项目**：本项目 (uni-app)，端口 5173

## 许可证

MIT License
