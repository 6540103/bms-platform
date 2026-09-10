<script setup>
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'

onLaunch(() => {
  console.log('BMS App Launch')
})

onShow(() => {
  console.log('App Show')
})

onHide(() => {
  console.log('App Hide')
})
</script>

<style lang="scss">
@import 'uview-plus/index.scss';

page {
  background-color: #0f0f1a;
  color: #e0e0e0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 通用卡片样式 */
.card {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 16rpx;
  padding: 24rpx;
  margin: 16rpx;
  border: 1rpx solid rgba(0, 212, 255, 0.1);
}

.card-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #00d4ff;
  margin-bottom: 16rpx;
}

/* 数据卡片 */
.data-card {
  background: rgba(26, 26, 46, 0.8);
  border-radius: 12rpx;
  padding: 20rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.05);
}

.data-value {
  font-size: 36rpx;
  font-weight: 700;
  color: #ffffff;
}

.data-label {
  font-size: 22rpx;
  color: #8b8b9e;
  margin-top: 4rpx;
}

.data-unit {
  font-size: 22rpx;
  color: #8b8b9e;
  margin-left: 4rpx;
}

/* 状态徽章 */
.status-badge {
  display: inline-block;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
  font-weight: 500;
}

.status-normal {
  background: rgba(0, 200, 83, 0.2);
  color: #00c853;
  border: 1rpx solid rgba(0, 200, 83, 0.3);
}

.status-warning {
  background: rgba(255, 171, 0, 0.2);
  color: #ffab00;
  border: 1rpx solid rgba(255, 171, 0, 0.3);
}

.status-alarm {
  background: rgba(255, 82, 82, 0.2);
  color: #ff5252;
  border: 1rpx solid rgba(255, 82, 82, 0.3);
}

.status-fault {
  background: rgba(156, 39, 176, 0.2);
  color: #ce93d8;
  border: 1rpx solid rgba(156, 39, 176, 0.3);
}
</style>
