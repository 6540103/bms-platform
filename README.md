# BMS 电池管理系统 - 完整项目

基于 RuoYi 框架开发的 BMS（Battery Management System，电池管理系统）完整项目，包含后端、Web前端、移动端APP三部分。

## 项目架构

```
bms-platform/
├── ruoyi-backend/      # 后端服务 (Spring Boot + RuoYi)
├── ruoyi-vue3/         # Web管理端 (Vue3 + Vite + Element Plus)
├── bms-uniapp/         # 移动端APP (uni-app + Vue3)
├── simulation/          # 电池仿真程序 (Python)
├── uploadPath/          # 文件上传目录
├── docker-compose.yml   # Docker编排文件
└── bms_uniapp_context.md  # 移动端需求文档
```

## 各模块说明

### 1. 后端服务 (ruoyi-backend)

- **技术栈**：Spring Boot 3.x + RuoYi + MyBatis + MySQL
- **端口**：8080
- **功能**：用户权限管理、BMS实时数据接口、历史数据查询、告警管理
- **API文档**：http://192.168.1.26:8080/swagger-ui.html

#### 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/bms/realtime/latest` | GET | 获取最新实时数据 |
| `/bms/realtime/list` | GET | 分页获取历史数据 |
| `/bms/realtime/{id}` | GET | 获取单条数据详情 |

#### 启动方式

```bash
cd ruoyi-backend
# 方式1：Maven启动
mvn spring-boot:run -pl ruoyi-admin
# 方式2：打包后启动
mvn clean package
java -jar ruoyi-admin/target/ruoyi-admin.jar
```

### 2. Web管理端 (ruoyi-vue3)

- **技术栈**：Vue 3 + Vite + Element Plus + Pinia
- **端口**：8081
- **功能**：系统管理、BMS数据监控仪表盘、历史数据查询、告警管理、电池详情

#### 启动方式

```bash
cd ruoyi-vue3
npm install
npm run dev
```

访问：http://localhost:8081 或 http://192.168.1.26:8081

默认账号：admin / admin123

### 3. 移动端APP (bms-uniapp)

- **技术栈**：uni-app + Vue 3 + Vite + uview-plus
- **端口**：5173 (H5开发模式)
- **支持平台**：H5、微信小程序、Android、iOS
- **功能**：实时监控仪表盘、电池详情（13单体）、历史数据、告警记录、设置

#### 页面列表

| 页面 | 路径 | 功能 |
|------|------|------|
| 实时监控 | `/pages/dashboard/index` | SOC、电压、电流、温度、单体电压、BMS状态 |
| 电池详情 | `/pages/battery/index` | 13单体详情、电压分布、极值统计 |
| 历史数据 | `/pages/history/index` | 时间筛选、趋势图、数据列表 |
| 告警记录 | `/pages/alarm/index` | 告警统计、筛选、保护类型说明 |
| 设置 | `/pages/settings/index` | 刷新间隔、API配置、数据管理 |

#### 启动方式

```bash
cd bms-uniapp
npm install
# H5开发
npm run dev:h5
# 微信小程序开发
npm run dev:mp-weixin
# H5生产构建
npm run build:h5
```

访问：http://localhost:5173 或 http://192.168.1.26:5173

### 4. 仿真程序 (simulation)

- **技术栈**：Python
- **功能**：电池数据仿真算法，模拟BMS实时数据生成

## 电池参数

- 电池类型：三元锂 13S1P
- 标称电压：48V
- 容量：40Ah
- 单体数量：13个
- 参考型号：九号电动 48V 电池

## 环境要求

| 软件 | 版本要求 |
|------|----------|
| JDK | 17+ |
| Maven | 3.8+ |
| Node.js | 18+ |
| npm | 9+ |
| MySQL | 8.0+ |
| Redis | 6.0+ |

## 快速开始

### 1. 数据库准备

```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE ry DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

# 导入数据
mysql -u root -p ry < ruoyi-backend/sql/ry_20250101.sql
```

### 2. 启动后端

```bash
cd ruoyi-backend
mvn clean package
java -jar ruoyi-admin/target/ruoyi-admin.jar
```

### 3. 启动Web前端

```bash
cd ruoyi-vue3
npm install
npm run dev
```

### 4. 启动移动端H5

```bash
cd bms-uniapp
npm install
npm run dev:h5
```

## 访问地址汇总

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端API | http://192.168.1.26:8080 | Spring Boot 服务 |
| Web管理端 | http://192.168.1.26:8081 | Vue3 管理页面 |
| 移动端H5 | http://192.168.1.26:5173 | uni-app H5页面 |
| API文档 | http://192.168.1.26:8080/swagger-ui.html | Swagger接口文档 |

## 技术架构图

```
┌─────────────────────────────────────────────────────┐
│                      客户端层                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Web管理端    │  │  移动端APP    │  │  小程序    │ │
│  │  (Vue3)      │  │  (uni-app)   │  │  (微信)    │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘ │
└─────────┼───────────────────┼──────────────────┼───────┘
          │                   │                  │
          └───────────────────┼──────────────────┘
                              │ HTTP/HTTPS
                              ▼
┌─────────────────────────────────────────────────────┐
│                    后端服务层                          │
│  ┌──────────────────────────────────────────────┐   │
│  │           Spring Boot + RuoYi                 │   │
│  │  ┌─────────┐ ┌─────────┐ ┌────────────────┐ │   │
│  │  │ 权限管理 │ │ BMS模块 │ │  系统管理模块   │ │   │
│  │  └─────────┘ └─────────┘ └────────────────┘ │   │
│  └──────────────────────────────────────────────┘   │
└─────────┬───────────────────┬───────────────────────┘
          │                   │
          ▼                   ▼
┌─────────────────┐  ┌─────────────────┐
│   MySQL 数据库   │  │   Redis 缓存    │
│   (ry数据库)     │  │   (会话/缓存)   │
└─────────────────┘  └─────────────────┘
```

## 开发规范

- 后端遵循阿里巴巴Java开发手册
- 前端使用ESLint + Prettier代码规范
- Git提交信息使用Conventional Commits规范
- 接口返回统一格式：`{code: 200, msg: "操作成功", data: {...}}`

## 许可证

MIT License
