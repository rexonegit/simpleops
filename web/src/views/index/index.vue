<template>
  <div class="index-container">
    <el-row :gutter="20">
      <el-col :lg="24" :md="24" :sm="24" :xl="24" :xs="24">
        <el-card class="card" shadow="never">
          <div slot="header">
            <span>依赖信息</span>
          </div>
          <div class="dependency-content">
            <div class="dependency-grid">
              <div class="dependency-item">
                <div class="dependency-info">
                  <div class="dependency-name">Vue版本</div>
                  <div class="dependency-version">{{ dependencies["vue"] }}</div>
                </div>
              </div>
              <div class="dependency-item">
                <div class="dependency-info">
                  <div class="dependency-name">Vuex版本</div>
                  <div class="dependency-version">{{ dependencies["vuex"] }}</div>
                </div>
              </div>
              <div class="dependency-item">
                <div class="dependency-info">
                  <div class="dependency-name">Vue Router</div>
                  <div class="dependency-version">{{ dependencies["vue-router"] }}</div>
                </div>
              </div>
              <div class="dependency-item">
                <div class="dependency-info">
                  <div class="dependency-name">Element Plus</div>
                  <div class="dependency-version">{{ dependencies["element-plus"] }}</div>
                </div>
              </div>
              <div class="dependency-item">
                <div class="dependency-info">
                  <div class="dependency-name">Axios版本</div>
                  <div class="dependency-version">{{ dependencies["axios"] }}</div>
                </div>
              </div>
              <div class="dependency-item">
                <div class="dependency-info">
                  <div class="dependency-name">Sass版本</div>
                  <div class="dependency-version">{{ devDependencies["sass"] }}</div>
                </div>
              </div>
            </div>
            <div class="system-info">
              <div class="info-header">
                <el-icon><InfoFilled /></el-icon>
                <span>系统信息</span>
              </div>
              <div class="info-content">
                <div class="info-item">
                  <span class="info-label">构建时间:</span>
                  <span class="info-value">{{ updateTime || "未知" }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">运行环境:</span>
                  <span class="info-value">{{ nodeEnv }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">用户代理:</span>
                  <span class="info-value">{{ userAgent }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { dependencies, devDependencies } from "../../../package.json";
import { InfoFilled } from "@element-plus/icons-vue";

export default {
  name: "Index",
  components: {
    InfoFilled,
  },
  data() {
    return {
      updateTime: process.env.VUE_APP_UPDATE_TIME,
      nodeEnv: process.env.NODE_ENV,
      dependencies: dependencies,
      devDependencies: devDependencies,
      userAgent: navigator.userAgent,
    };
  },
};
</script>

<style lang="scss" scoped>
.index-container {
  padding: 0 !important;
  margin: 0 !important;
  background: #f5f7f8 !important;

  .card {
    min-height: 400px;
    display: flex;
    flex-direction: column;

    :deep() {
      .el-card__body {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
    }

    .dependency-content {
      height: 100%;
      display: flex;
      flex-direction: column;
      overflow-y: auto;

      .dependency-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-bottom: 25px;
        flex-shrink: 0;

        .dependency-item {
          display: flex;
          align-items: center;
          padding: 15px;
          background: #f8f9fa;
          border: 1px solid #e9ecef;
          border-radius: 8px;
          transition: all 0.3s ease;

          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            background: #ffffff;
          }

          .dependency-info {
            flex: 1;
            text-align: center;

            .dependency-name {
              font-size: 0.9rem;
              color: #6c757d;
              margin-bottom: 6px;
              font-weight: 500;
            }

            .dependency-version {
              font-size: 1.1rem;
              color: #2c3e50;
              font-weight: 600;
            }
          }
        }
      }

      .system-info {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 20px;
        flex-shrink: 0;

        .info-header {
          display: flex;
          align-items: center;
          margin-bottom: 15px;
          padding-bottom: 10px;
          border-bottom: 2px solid #dee2e6;

          .el-icon {
            color: #409eff;
            margin-right: 8px;
            font-size: 1.2rem;
          }

          span {
            font-size: 1.1rem;
            font-weight: 600;
            color: #2c3e50;
          }
        }

        .info-content {
          .info-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #f1f3f4;

            &:last-child {
              border-bottom: none;
            }

            .info-label {
              color: #6c757d;
              font-weight: 500;
              font-size: 0.9rem;
            }

            .info-value {
              color: #2c3e50;
              font-weight: 600;
              font-size: 0.9rem;
              max-width: 60%;
              text-align: right;
              word-break: break-all;
            }
          }
        }
      }
    }
  }
}
</style>
