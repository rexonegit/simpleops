<template>
  <div class="baremetal-container">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input v-model="searchQuery" placeholder="搜索主机名、项目、IP、序列号、资产编号..." clearable style="width: 360px; margin-right: 10px;" @keyup.enter="handleSearch" />
      <el-button type="primary" @click="handleSearch"><el-icon style="margin-right: 4px;"><Search /></el-icon>搜索</el-button>
      <el-button type="primary" @click="openCreateDialog" style="margin-left: 8px;"><el-icon style="margin-right: 4px;"><Plus /></el-icon>新建</el-button>
    </div>

    <!-- 环境类型统计卡片 -->
    <div class="env-stat-row">
      <div v-for="card in envCards" :key="card.key" class="env-stat-card" :class="{ active: activeEnvFilter === card.key }" @click="filterByEnv(card.key)">
        <el-icon class="env-icon" :class="card.key"><component :is="card.icon" /></el-icon>
        <span class="env-label">{{ card.label }}</span>
        <span class="env-count" :class="card.key">{{ card.key === 'all' ? envStats.total : (envStats[card.key] || 0) }}</span>
      </div>
    </div>

    <!-- 保修状态筛选标签 -->
    <div class="warranty-filter-row">
      <div class="warranty-filter-card" :class="{ active: activeWarrantyFilter === 'all' }" @click="filterByWarranty('all')">
        <el-icon class="warranty-icon"><Monitor /></el-icon>
        <span class="warranty-label">全部保修状态</span>
        <span class="warranty-count">{{ warrantyStats.total }}</span>
      </div>
      <div class="warranty-filter-card warning" :class="{ active: activeWarrantyFilter === 'expiring_soon' }" @click="filterByWarranty('expiring_soon')">
        <el-icon class="warranty-icon"><AlarmClock /></el-icon>
        <span class="warranty-label">即将过期 (3个月内)</span>
        <span class="warranty-count warning">{{ warrantyStats.expiring_soon }}</span>
      </div>
      <div class="warranty-filter-card danger" :class="{ active: activeWarrantyFilter === 'expired' }" @click="filterByWarranty('expired')">
        <el-icon class="warranty-icon"><WarningIcon /></el-icon>
        <span class="warranty-label">已经过保</span>
        <span class="warranty-count danger">{{ warrantyStats.expired }}</span>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-card style="margin-top: 20px;" class="table-card">
      <el-table v-loading="listLoading" :data="baremetalList" style="width: 100%" stripe border :key="tableKey">
        <el-table-column prop="hostname" label="主机名" min-width="150" sortable show-overflow-tooltip />
        <el-table-column prop="ip_address" label="业务IP" min-width="130" sortable show-overflow-tooltip />
        <el-table-column prop="project" label="所属项目" min-width="130" sortable show-overflow-tooltip />
        <el-table-column prop="environment" label="环境类型" min-width="100" sortable>
          <template #default="{ row }">
            <el-tag :type="envTagType(row.environment)" size="small">{{ getEnvLabel(row.environment) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" min-width="90" sortable />
        <el-table-column prop="vendor" label="厂商" min-width="90" sortable show-overflow-tooltip />
        <el-table-column prop="model" label="型号" min-width="140" sortable show-overflow-tooltip />
        <el-table-column prop="os_name" label="操作系统" min-width="130" sortable show-overflow-tooltip />
        <el-table-column prop="data_center" label="数据中心" min-width="100" sortable />
        <el-table-column prop="warranty_expire" label="保修到期" min-width="110" sortable>
          <template #default="{ row }">
            <span :class="{ 'text-danger': isExpiring(row.warranty_expire) }">{{ formatDateShort(row.warranty_expire) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDetailDialog(row)"><el-icon style="margin-right: 2px;"><View /></el-icon>详情</el-button>
            <el-button type="primary" link size="small" @click="openEditDialog(row)"><el-icon style="margin-right: 2px;"><Edit /></el-icon>编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteItem(row)"><el-icon style="margin-right: 2px;"><Delete /></el-icon>删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-container">
        <el-pagination :current-page="currentPage" :page-sizes="[10, 20, 50, 100]" :page-size="pageSize" :total="total" layout="total, sizes, prev, pager, next, jumper" @size-change="handleSizeChange" @current-change="handleCurrentChange" />
      </div>
    </el-card>

    <!-- ========== 编辑/创建弹窗（使用 el-form） ========== -->
    <el-dialog
      :title="dialogMode === 'create' ? '新增物理机' : '编辑物理机'"
      v-model="formDialogVisible"
      width="960px"
      destroy-on-close
      top="3vh"
      :close-on-click-modal="false"
      class="custom-dialog"
      v-if="dialogMode !== 'detail'"
    >
      <div class="form-container" v-loading="formLoading">
        <el-form ref="formRef" :model="currentFormData" :rules="formRules" label-width="120px" class="custom-form">

          <!-- 基础信息 -->
          <div class="group-block">
            <div class="group-header">
              <span class="group-title">基础信息</span>
            </div>
            <div class="group-content">
              <el-row :gutter="24">
                <el-col :span="12">
                  <el-form-item label="主机名" prop="hostname"><el-input v-model="currentFormData.hostname" placeholder="请输入" /></el-form-item>
                  <el-form-item label="业务IP" prop="ip_address"><el-input v-model="currentFormData.ip_address" placeholder="请输入" /></el-form-item>
                  <el-form-item label="所属项目" prop="project"><el-input v-model="currentFormData.project" placeholder="请输入" /></el-form-item>
                  <el-form-item label="环境类型" prop="environment">
                    <el-select v-model="currentFormData.environment" placeholder="请选择" style="width: 100%">
                      <el-option v-for="item in environmentOptions" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="负责人"><el-input v-model="currentFormData.owner" placeholder="请输入" /></el-form-item>
                  <el-form-item label="部门">
                    <el-select v-model="currentFormData.department" placeholder="请选择或输入" style="width: 100%" filterable allow-create clearable>
                      <el-option v-for="dept in departmentOptions" :key="dept" :label="dept" :value="dept" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="资产编号"><el-input v-model="currentFormData.asset_code" placeholder="请输入" /></el-form-item>
                  <el-form-item label="厂商">
                    <el-select v-model="currentFormData.vendor" placeholder="请选择或输入" style="width: 100%" filterable allow-create clearable>
                      <el-option v-for="v in vendorOptions" :key="v" :label="v" :value="v" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="型号"><el-input v-model="currentFormData.model" placeholder="请输入" /></el-form-item>
                  <el-form-item label="设备类型">
                    <el-select v-model="currentFormData.device_type" placeholder="请选择或输入" style="width: 100%" filterable allow-create clearable>
                      <el-option v-for="dt in deviceTypeOptions" :key="dt" :label="dt" :value="dt" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="序列号"><el-input v-model="currentFormData.serial_number" placeholder="请输入" /></el-form-item>
                  <el-form-item label="快速服务代码"><el-input v-model="currentFormData.express_service_code" placeholder="请输入" /></el-form-item>
                  <el-form-item label="数据中心">
                    <el-select v-model="currentFormData.data_center" placeholder="请选择或输入" style="width: 100%" filterable allow-create clearable>
                      <el-option v-for="dc in dataCenterOptions" :key="dc" :label="dc" :value="dc" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="U数"><el-input v-model="currentFormData.u_count" placeholder="如2U" /></el-form-item>
                  <el-form-item label="机柜位置"><el-input v-model="currentFormData.rack_position" placeholder="如U01-U02" /></el-form-item>
                  <el-form-item label="所属机柜"><el-input v-model="currentFormData.cabinet" placeholder="请输入" /></el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="24">
                <el-col :span="12">
                  <el-form-item label="所属机房"><el-input v-model="currentFormData.room" placeholder="请输入" /></el-form-item>
                  <el-form-item label="生产日期">
                    <el-date-picker v-model="currentFormData.production_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
                  </el-form-item>
                  <el-form-item label="保修到期">
                    <el-date-picker v-model="currentFormData.warranty_expire" type="date" placeholder="选择日期" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="上架时间">
                    <el-date-picker v-model="currentFormData.rack_time" type="date" placeholder="选择日期" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="说明" class="full-width"><el-input v-model="currentFormData.description" type="textarea" :rows="2" placeholder="请输入说明" /></el-form-item>
            </div>
          </div>

          <!-- 硬件信息 -->
          <div class="group-block">
            <div class="group-header">
              <span class="group-title">硬件信息</span>
            </div>
            <div class="group-content">
              <el-row :gutter="24">
                <el-col :span="12">
                  <el-form-item label="CPU型号"><el-input v-model="currentFormData.cpu_model" placeholder="如Intel Xeon Gold 6248" /></el-form-item>
                  <el-form-item label="CPU数量"><el-input v-model="currentFormData.cpu_count" placeholder="请输入" /></el-form-item>
                  <el-form-item label="CPU内核数"><el-input v-model="currentFormData.cpu_cores" placeholder="请输入" /></el-form-item>
                  <el-form-item label="逻辑处理器"><el-input v-model="currentFormData.cpu_logical_processors" placeholder="请输入" /></el-form-item>
                  <el-form-item label="内存总容量"><el-input v-model="currentFormData.memory_size" placeholder="如256GB" /></el-form-item>
                  <el-form-item label="内存组合"><el-input v-model="currentFormData.memory_detail" placeholder="如16GB DDR4 * 16" /></el-form-item>
                  <el-form-item label="磁盘概要"><el-input v-model="currentFormData.disk" placeholder="如2*480GB SSD + 4*2TB HDD" /></el-form-item>
                  <el-form-item label="阵列卡"><el-input v-model="currentFormData.raid_card" placeholder="请输入" /></el-form-item>
                  <el-form-item label="阵列配置"><el-input v-model="currentFormData.raid_config" placeholder="请输入" /></el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="热备盘"><el-input v-model="currentFormData.hot_spare_disk" placeholder="请输入" /></el-form-item>
                  <el-form-item label="虚拟磁盘"><el-input v-model="currentFormData.virtual_disk" placeholder="请输入" /></el-form-item>
                  <el-form-item label="硬盘外型">
                    <el-select v-model="currentFormData.disk_form_factor" placeholder="请选择" style="width: 100%" clearable>
                      <el-option label="2.5寸" value="2.5寸" /><el-option label="3.5寸" value="3.5寸" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="介质类型">
                    <el-select v-model="currentFormData.disk_media_type" placeholder="请选择" style="width: 100%" clearable>
                      <el-option label="SSD" value="SSD" /><el-option label="HDD" value="HDD" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="总线协议">
                    <el-select v-model="currentFormData.disk_bus_protocol" placeholder="请选择" style="width: 100%" clearable>
                      <el-option label="SATA" value="SATA" /><el-option label="SAS" value="SAS" /><el-option label="NVMe" value="NVMe" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="硬盘数量"><el-input v-model="currentFormData.disk_count" placeholder="请输入" /></el-form-item>
                  <el-form-item label="单盘大小"><el-input v-model="currentFormData.disk_capacity_per_disk" placeholder="如1.92TB" /></el-form-item>
                  <el-form-item label="GPU名称"><el-input v-model="currentFormData.gpu_name" placeholder="请输入" /></el-form-item>
                  <el-form-item label="GPU类型"><el-input v-model="currentFormData.gpu_type" placeholder="如NVIDIA Tesla T4" /></el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="GPU描述" class="full-width"><el-input v-model="currentFormData.gpu_desc" type="textarea" :rows="2" placeholder="请输入" /></el-form-item>
            </div>
          </div>

          <!-- 网络信息 -->
          <div class="group-block">
            <div class="group-header">
              <span class="group-title">网络信息</span>
            </div>
            <div class="group-content">
              <el-row :gutter="24">
                <el-col :span="8"><el-form-item label="板载网卡型号"><el-input v-model="currentFormData.onboard_nic_model" placeholder="请输入" /></el-form-item></el-col>
                <el-col :span="8"><el-form-item label="板载网卡速率"><el-input v-model="currentFormData.onboard_nic_speed" placeholder="如10Gbps" /></el-form-item></el-col>
                <el-col :span="8"><el-form-item label="板载网卡接口数"><el-input v-model="currentFormData.onboard_nic_ports" placeholder="请输入" /></el-form-item></el-col>
              </el-row>
              <el-row :gutter="24">
                <el-col :span="8"><el-form-item label="附加网卡型号"><el-input v-model="currentFormData.additional_nic_model" placeholder="请输入" /></el-form-item></el-col>
                <el-col :span="8"><el-form-item label="附加网卡速率"><el-input v-model="currentFormData.additional_nic_speed" placeholder="请输入" /></el-form-item></el-col>
                <el-col :span="8"><el-form-item label="附加网卡接口数"><el-input v-model="currentFormData.additional_nic_ports" placeholder="请输入" /></el-form-item></el-col>
              </el-row>
            </div>
          </div>

          <!-- 软件信息 -->
          <div class="group-block">
            <div class="group-header">
              <span class="group-title">软件信息</span>
            </div>
            <div class="group-content">
              <el-row :gutter="24">
                <el-col :span="12">
                  <!-- 左列：操作系统、操作系统版本、虚拟化IP、虚拟化用户名 -->
                  <el-form-item label="操作系统" prop="os_name">
                    <el-select v-model="currentFormData.os_name" placeholder="请选择或输入" style="width: 100%" filterable allow-create clearable>
                      <el-option v-for="os in osNameOptions" :key="os" :label="os" :value="os" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="操作系统版本"><el-input v-model="currentFormData.os_version" placeholder="请输入" /></el-form-item>
                  <el-form-item label="虚拟化IP"><el-input v-model="currentFormData.virtualization_ip" placeholder="请输入" /></el-form-item>
                  <el-form-item label="虚拟化用户名"><el-input v-model="currentFormData.virtualization_username" placeholder="请输入" /></el-form-item>
                </el-col>
                <el-col :span="12">
                  <!-- 右列：远程控制、虚拟化类型、虚拟化地址、虚拟化密码 -->
                  <el-form-item label="远程控制"><el-input v-model="currentFormData.remote_control" placeholder="请输入" /></el-form-item>
                  <el-form-item label="虚拟化类型">
                    <el-select v-model="currentFormData.virtualization_type" placeholder="请选择" style="width: 100%" clearable>
                      <el-option label="VMware" value="VMware" /><el-option label="KVM" value="KVM" />
                      <el-option label="Hyper-V" value="Hyper-V" /><el-option label="裸金属" value="裸金属" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="虚拟化地址"><el-input v-model="currentFormData.virtualization_address" placeholder="请输入" /></el-form-item>
                  <el-form-item label="虚拟化密码"><el-input v-model="currentFormData.virtualization_password" show-password placeholder="请输入" autoComplete="new-password" /></el-form-item>
                </el-col>
              </el-row>
            </div>
          </div>

          <!-- 管理信息 -->
          <div class="group-block">
            <div class="group-header">
              <span class="group-title">管理信息</span>
            </div>
            <div class="group-content">
              <el-row :gutter="24">
                <el-col :span="12">
                  <el-form-item label="管理IP"><el-input v-model="currentFormData.management_ip" placeholder="iDRAC/IPMI地址" /></el-form-item>
                  <el-form-item label="管理地址"><el-input v-model="currentFormData.management_address" placeholder="带外管理Web URL" /></el-form-item>
                  <el-form-item label="管理用户名"><el-input v-model="currentFormData.management_username" placeholder="请输入" /></el-form-item>
                  <el-form-item label="管理密码"><el-input v-model="currentFormData.management_password" show-password placeholder="请输入" autoComplete="new-password" /></el-form-item>
                  <el-form-item label="BIOS密码"><el-input v-model="currentFormData.bios_password" show-password placeholder="请输入" autoComplete="new-password" /></el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="主要维护人"><el-input v-model="currentFormData.operator" placeholder="请输入" /></el-form-item>
                  <el-form-item label="备份维护人"><el-input v-model="currentFormData.bak_operator" placeholder="请输入" /></el-form-item>
                  <el-form-item label="值班电话"><el-input v-model="currentFormData.duty_phone" placeholder="请输入" /></el-form-item>
                </el-col>
              </el-row>
            </div>
          </div>

        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="formDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="save()" :loading="formLoading">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- ========== 详情弹窗（使用 el-descriptions） ========== -->
    <el-dialog
      title="物理机详情"
      v-model="detailDialogVisible"
      width="960px"
      destroy-on-close
      top="3vh"
      :close-on-click-modal="false"
      class="custom-dialog detail-dialog"
    >
      <div class="detail-container" v-loading="formLoading">

        <!-- 基础信息 -->
        <div class="group-block">
          <div class="group-header">
            <span class="group-title">基础信息</span>
          </div>
          <div class="group-content">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="主机名">{{ currentFormData.hostname || '-' }}</el-descriptions-item>
              <el-descriptions-item label="业务IP">{{ currentFormData.ip_address || '-' }}</el-descriptions-item>
              <el-descriptions-item label="所属项目">{{ currentFormData.project || '-' }}</el-descriptions-item>
              <el-descriptions-item label="环境类型">
                <el-tag :type="envTagType(currentFormData.environment)" size="small">{{ getEnvLabel(currentFormData.environment) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="负责人">{{ currentFormData.owner || '-' }}</el-descriptions-item>
              <el-descriptions-item label="部门">{{ currentFormData.department || '-' }}</el-descriptions-item>
              <el-descriptions-item label="资产编号">{{ currentFormData.asset_code || '-' }}</el-descriptions-item>
              <el-descriptions-item label="厂商">{{ currentFormData.vendor || '-' }}</el-descriptions-item>
              <el-descriptions-item label="型号">{{ currentFormData.model || '-' }}</el-descriptions-item>
              <el-descriptions-item label="设备类型">{{ currentFormData.device_type || '-' }}</el-descriptions-item>
              <el-descriptions-item label="序列号">{{ currentFormData.serial_number || '-' }}</el-descriptions-item>
              <el-descriptions-item label="快速服务代码">{{ currentFormData.express_service_code || '-' }}</el-descriptions-item>
              <el-descriptions-item label="数据中心">{{ currentFormData.data_center || '-' }}</el-descriptions-item>
              <el-descriptions-item label="U数">{{ currentFormData.u_count || '-' }}</el-descriptions-item>
              <el-descriptions-item label="机柜位置">{{ currentFormData.rack_position || '-' }}</el-descriptions-item>
              <el-descriptions-item label="所属机柜">{{ currentFormData.cabinet || '-' }}</el-descriptions-item>
              <el-descriptions-item label="所属机房">{{ currentFormData.room || '-' }}</el-descriptions-item>
              <el-descriptions-item label="生产日期">{{ formatDateShort(currentFormData.production_date) }}</el-descriptions-item>
              <el-descriptions-item label="保修到期">{{ formatDateShort(currentFormData.warranty_expire) }}</el-descriptions-item>
              <el-descriptions-item label="上架时间">{{ formatDateShort(currentFormData.rack_time) }}</el-descriptions-item>
              <el-descriptions-item label="说明" :span="2">{{ currentFormData.description || '-' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <!-- 硬件信息 -->
        <div class="group-block">
          <div class="group-header">
            <span class="group-title">硬件信息</span>
          </div>
          <div class="group-content">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="CPU型号">{{ currentFormData.cpu_model || '-' }}</el-descriptions-item>
              <el-descriptions-item label="CPU数量">{{ currentFormData.cpu_count || '-' }}</el-descriptions-item>
              <el-descriptions-item label="CPU内核数">{{ currentFormData.cpu_cores || '-' }}</el-descriptions-item>
              <el-descriptions-item label="逻辑处理器">{{ currentFormData.cpu_logical_processors || '-' }}</el-descriptions-item>
              <el-descriptions-item label="内存总容量">{{ currentFormData.memory_size || '-' }}</el-descriptions-item>
              <el-descriptions-item label="内存组合">{{ currentFormData.memory_detail || '-' }}</el-descriptions-item>
              <el-descriptions-item label="磁盘概要">{{ currentFormData.disk || '-' }}</el-descriptions-item>
              <el-descriptions-item label="阵列卡">{{ currentFormData.raid_card || '-' }}</el-descriptions-item>
              <el-descriptions-item label="阵列配置">{{ currentFormData.raid_config || '-' }}</el-descriptions-item>
              <el-descriptions-item label="热备盘">{{ currentFormData.hot_spare_disk || '-' }}</el-descriptions-item>
              <el-descriptions-item label="虚拟磁盘">{{ currentFormData.virtual_disk || '-' }}</el-descriptions-item>
              <el-descriptions-item label="硬盘外型">{{ currentFormData.disk_form_factor || '-' }}</el-descriptions-item>
              <el-descriptions-item label="介质类型">{{ currentFormData.disk_media_type || '-' }}</el-descriptions-item>
              <el-descriptions-item label="总线协议">{{ currentFormData.disk_bus_protocol || '-' }}</el-descriptions-item>
              <el-descriptions-item label="硬盘数量">{{ currentFormData.disk_count || '-' }}</el-descriptions-item>
              <el-descriptions-item label="单盘大小">{{ currentFormData.disk_capacity_per_disk || '-' }}</el-descriptions-item>
              <el-descriptions-item label="GPU名称">{{ currentFormData.gpu_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="GPU类型">{{ currentFormData.gpu_type || '-' }}</el-descriptions-item>
              <el-descriptions-item label="GPU描述" :span="2">{{ currentFormData.gpu_desc || '-' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <!-- 网络信息 -->
        <div class="group-block">
          <div class="group-header">
            <span class="group-title">网络信息</span>
          </div>
          <div class="group-content">
            <el-descriptions :column="3" border>
              <el-descriptions-item label="板载网卡型号">{{ currentFormData.onboard_nic_model || '-' }}</el-descriptions-item>
              <el-descriptions-item label="板载网卡速率">{{ currentFormData.onboard_nic_speed || '-' }}</el-descriptions-item>
              <el-descriptions-item label="板载网卡接口数">{{ currentFormData.onboard_nic_ports || '-' }}</el-descriptions-item>
              <el-descriptions-item label="附加网卡型号">{{ currentFormData.additional_nic_model || '-' }}</el-descriptions-item>
              <el-descriptions-item label="附加网卡速率">{{ currentFormData.additional_nic_speed || '-' }}</el-descriptions-item>
              <el-descriptions-item label="附加网卡接口数">{{ currentFormData.additional_nic_ports || '-' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <!-- 软件信息 -->
        <div class="group-block">
          <div class="group-header">
            <span class="group-title">软件信息</span>
          </div>
          <div class="group-content">
            <el-descriptions :column="2" border>
              <!-- 第一行：操作系统 | 远程控制 -->
              <el-descriptions-item label="操作系统">{{ currentFormData.os_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="远程控制">{{ currentFormData.remote_control || '-' }}</el-descriptions-item>

              <!-- 第二行：操作系统版本 | 虚拟化类型 -->
              <el-descriptions-item label="操作系统版本">{{ currentFormData.os_version || '-' }}</el-descriptions-item>
              <el-descriptions-item label="虚拟化类型">{{ currentFormData.virtualization_type || '-' }}</el-descriptions-item>

              <!-- 第三行：虚拟化IP | 虚拟化地址 -->
              <el-descriptions-item label="虚拟化IP">{{ currentFormData.virtualization_ip || '-' }}</el-descriptions-item>
              <el-descriptions-item label="虚拟化地址">
                <a
                  v-if="currentFormData.virtualization_address"
                  :href="formatUrl(currentFormData.virtualization_address)"
                  target="_blank"
                  class="link-address"
                >
                  <el-icon><Link /></el-icon>
                  {{ currentFormData.virtualization_address }}
                </a>
                <span v-else>-</span>
              </el-descriptions-item>

              <!-- 第四行：虚拟化用户名 | 虚拟化密码 -->
              <el-descriptions-item label="虚拟化用户名">{{ currentFormData.virtualization_username || '-' }}</el-descriptions-item>
              <el-descriptions-item label="虚拟化密码">
                <div class="password-field-inline">
                  <span class="password-text" :class="{ 'is-visible': passwordVisibility.virtualization }">
                    {{ passwordVisibility.virtualization ? currentFormData.virtualization_password : '******' }}
                  </span>
                  <div class="password-actions-inline">
                    <el-tooltip :content="passwordVisibility.virtualization ? '隐藏' : '查看'" placement="top">
                      <el-icon class="action-btn" @click="togglePasswordVisibility('virtualization')">
                        <View v-if="!passwordVisibility.virtualization" />
                        <Hide v-else />
                      </el-icon>
                    </el-tooltip>
                    <el-tooltip content="复制" placement="top">
                      <el-icon class="action-btn copy-btn" @click="copyPassword(currentFormData.virtualization_password)">
                        <CopyDocument />
                      </el-icon>
                    </el-tooltip>
                  </div>
                </div>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <!-- 管理信息 -->
        <div class="group-block">
          <div class="group-header">
            <span class="group-title">管理信息</span>
          </div>
          <div class="group-content">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="管理IP">{{ currentFormData.management_ip || '-' }}</el-descriptions-item>

              <!-- 管理地址 - 可点击链接 -->
              <el-descriptions-item label="管理地址">
                <a
                  v-if="currentFormData.management_address"
                  :href="formatUrl(currentFormData.management_address)"
                  target="_blank"
                  class="link-address"
                >
                  <el-icon><Link /></el-icon>
                  {{ currentFormData.management_address }}
                </a>
                <span v-else>-</span>
              </el-descriptions-item>

              <el-descriptions-item label="管理用户名">{{ currentFormData.management_username || '-' }}</el-descriptions-item>

              <!-- 管理密码 - 直接显示/隐藏 -->
              <el-descriptions-item label="管理密码">
                <div class="password-field-inline">
                  <span class="password-text" :class="{ 'is-visible': passwordVisibility.management }">
                    {{ passwordVisibility.management ? currentFormData.management_password : '******' }}
                  </span>
                  <div class="password-actions-inline">
                    <el-tooltip :content="passwordVisibility.management ? '隐藏' : '查看'" placement="top">
                      <el-icon class="action-btn" @click="togglePasswordVisibility('management')">
                        <View v-if="!passwordVisibility.management" />
                        <Hide v-else />
                      </el-icon>
                    </el-tooltip>
                    <el-tooltip content="复制" placement="top">
                      <el-icon class="action-btn copy-btn" @click="copyPassword(currentFormData.management_password)">
                        <CopyDocument />
                      </el-icon>
                    </el-tooltip>
                  </div>
                </div>
              </el-descriptions-item>

              <!-- BIOS密码 - 直接显示/隐藏 -->
              <el-descriptions-item label="BIOS密码">
                <div class="password-field-inline">
                  <span class="password-text" :class="{ 'is-visible': passwordVisibility.bios }">
                    {{ passwordVisibility.bios ? currentFormData.bios_password : '******' }}
                  </span>
                  <div class="password-actions-inline">
                    <el-tooltip :content="passwordVisibility.bios ? '隐藏' : '查看'" placement="top">
                      <el-icon class="action-btn" @click="togglePasswordVisibility('bios')">
                        <View v-if="!passwordVisibility.bios" />
                        <Hide v-else />
                      </el-icon>
                    </el-tooltip>
                    <el-tooltip content="复制" placement="top">
                      <el-icon class="action-btn copy-btn" @click="copyPassword(currentFormData.bios_password)">
                        <CopyDocument />
                      </el-icon>
                    </el-tooltip>
                  </div>
                </div>
              </el-descriptions-item>

              <el-descriptions-item label="主要维护人">{{ currentFormData.operator || '-' }}</el-descriptions-item>
              <el-descriptions-item label="备份维护人">{{ currentFormData.bak_operator || '-' }}</el-descriptions-item>
              <el-descriptions-item label="值班电话">{{ currentFormData.duty_phone || '-' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <!-- 系统信息 -->
        <div class="group-block">
          <div class="group-header">
            <span class="group-title">系统信息</span>
          </div>
          <div class="group-content">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="创建时间">{{ formatDateTime(currentFormData.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatDateTime(currentFormData.updated_at) }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="editFromDetail">编辑</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 删除确认 -->
    <el-dialog title="删除确认" v-model="deleteDialogVisible" width="500px" destroy-on-close>
      <div style="margin-bottom: 20px;">
        <el-icon style="color: #E6A23C; font-size: 24px; vertical-align: middle;"><WarningIcon /></el-icon>
        <span style="vertical-align: middle; margin-left: 10px;">确定要删除物理机 <strong>{{ deleteItemData.hostname }}</strong> 吗？</span>
      </div>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search, Plus, Monitor, SwitchButton, VideoPlay, Connection, Clock, SetUp,
  AlarmClock, Warning as WarningIcon, Edit, Delete, View, Hide, Setting,
  CopyDocument, Cpu, Link
} from '@element-plus/icons-vue'
import {
  listProjectBareMetal, getProjectBareMetal,
  createProjectBareMetal, updateProjectBareMetal, deleteProjectBareMetal
} from '@/api/datacenter/projectbaremetal'

// ===== 状态 =====
const tableKey = ref(0), listLoading = ref(true), baremetalList = ref([])
const total = ref(0), currentPage = ref(1), pageSize = ref(10)
const searchQuery = ref(''), activeEnvFilter = ref('all')
const activeWarrantyFilter = ref('all')
const envStats = ref({ total: 0 })
const warrantyStats = ref({ total: 0, expiring_soon: 0, expired: 0 })

// 弹窗状态
const formDialogVisible = ref(false)      // 编辑/创建弹窗
const detailDialogVisible = ref(false)    // 详情弹窗
const deleteDialogVisible = ref(false)
const dialogMode = ref('create')          // 'create' | 'edit' | 'detail'
const formLoading = ref(false)
const deleteItemData = ref({})
const formRef = ref(null)

// 密码可见性状态（详情页使用）
const passwordVisibility = ref({
  virtualization: false,
  management: false,
  bios: false
})

// ===== 选项配置 =====
const envCards = [
  { key: 'all', label: '总数', icon: Monitor }, { key: 'prod', label: '生产环境', icon: Monitor },
  { key: 'stg', label: '预发布', icon: Monitor }, { key: 'uat', label: 'UAT', icon: Monitor },
  { key: 'test', label: '测试环境', icon: Monitor }, { key: 'dev', label: '开发环境', icon: Monitor },
  { key: 'other', label: '其他', icon: WarningIcon },
]
const environmentOptions = [
  { label: '生产环境', value: 'prod' }, { label: '测试环境', value: 'test' }, { label: '开发环境', value: 'dev' },
  { label: '用户验收环境', value: 'uat' }, { label: '预生产环境', value: 'stg' }, { label: '灾备环境', value: 'dr' }, { label: '其他', value: 'other' }
]
const departmentOptions = ['数据组', '研发组', '产品组', '运维组']
const vendorOptions = ['Dell', 'HPE', 'Lenovo', '浪潮', '华为', '超微', '联想']
const deviceTypeOptions = ['机架式服务器', '台式机', '安全设备', '塔式服务器', '刀片服务器', '高密度服务器', 'GPU服务器', '存储服务器']
const dataCenterOptions = []
const osNameOptions = ['VMware ESXi', 'Proxmox VE', 'Rocky Linux', 'Windows Server', 'CentOS', 'Red Hat Enterprise Linux', 'Ubuntu', 'Debian', 'openSUSE', 'AlmaLinux']

// ===== 默认表单对象 =====
const getDefaultItem = () => ({
  id: null,
  // 基础信息
  hostname: '', ip_address: '', project: '', environment: 'prod', owner: '', department: '',
  asset_code: '', vendor: '', model: '', device_type: '', serial_number: '', express_service_code: '',
  data_center: '', u_count: '', rack_position: '', cabinet: '', room: '',
  production_date: null, warranty_expire: null, rack_time: null, description: '',
  // 硬件信息
  cpu_model: '', cpu_count: '', cpu_cores: '', cpu_logical_processors: '',
  memory_size: '', memory_detail: '', disk: '',
  raid_card: '', raid_config: '', hot_spare_disk: '', virtual_disk: '',
  disk_form_factor: '', disk_media_type: '', disk_bus_protocol: '', disk_count: '', disk_capacity_per_disk: '',
  gpu_name: '', gpu_type: '', gpu_desc: '',
  // 网络信息
  onboard_nic_model: '', onboard_nic_speed: '', onboard_nic_ports: '',
  additional_nic_model: '', additional_nic_speed: '', additional_nic_ports: '',
  // 软件信息
  os_name: '', os_version: '', virtualization_type: '', virtualization_ip: '',
  virtualization_address: '', virtualization_username: '', virtualization_password: '',
  // 管理信息
  management_ip: '', management_address: '', management_username: '', management_password: '',
  bios_password: '', remote_control: '', operator: '', bak_operator: '', duty_phone: '',
  // 系统信息
  created_at: null, updated_at: null,
})

const currentFormData = ref(getDefaultItem())

const formRules = {
  hostname: [{ required: true, message: '主机名不能为空', trigger: 'blur' }],
  ip_address: [{ required: true, message: '业务IP不能为空', trigger: 'blur' }],
  project: [{ required: true, message: '所属项目不能为空', trigger: 'blur' }],
  environment: [{ required: true, message: '请选择环境类型', trigger: 'change' }],
  os_name: [{ required: true, message: '操作系统不能为空', trigger: 'blur' }],
}

// ===== 数据加载 =====
const fetchData = async () => {
  listLoading.value = true
  try {
    // 如果有过保筛选，需要获取全部数据进行客户端筛选
    const needAllData = activeWarrantyFilter.value !== 'all'
    const params = { page: needAllData ? 1 : currentPage.value, pageSize: needAllData ? 9999 : pageSize.value, search: searchQuery.value }
    if (activeEnvFilter.value !== 'all') params.environment = activeEnvFilter.value
    const res = await listProjectBareMetal(params)
    const payload = res.data || res
    let listData = payload.results || payload.list || payload.data || []

    // 保修状态筛选（客户端筛选）
    if (activeWarrantyFilter.value === 'expiring_soon') {
      listData = listData.filter(item => {
        if (!item.warranty_expire) return false
        const daysLeft = Math.ceil((new Date(item.warranty_expire) - new Date()) / (1000 * 3600 * 24))
        return daysLeft > 0 && daysLeft <= 90
      })
    } else if (activeWarrantyFilter.value === 'expired') {
      listData = listData.filter(item => {
        if (!item.warranty_expire) return false
        const expireDate = new Date(item.warranty_expire); const today = new Date()
        today.setHours(0, 0, 0, 0); expireDate.setHours(0, 0, 0, 0)
        return expireDate < today
      })
    }

    // 如果获取了全部数据，需要手动分页
    if (needAllData) {
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      total.value = listData.length
      baremetalList.value = listData.slice(start, end)
    } else {
      baremetalList.value = listData
      total.value = payload.count || payload.total || listData.length
    }

    await fetchEnvStats()
  } catch (err) {
    console.error('数据加载失败', err); ElMessage.error('数据加载失败'); baremetalList.value = []
  } finally { listLoading.value = false; tableKey.value++ }
}

const fetchEnvStats = async () => {
  try {
    const res = await listProjectBareMetal({ pageSize: 9999 })
    const payload = res.data || res
    const allData = payload.results || payload.list || payload.data || []
    const counts = {}
    allData.forEach(item => { const env = item.environment || 'other'; counts[env] = (counts[env] || 0) + 1 })
    envStats.value = { total: allData.length, ...counts }
    warrantyStats.value = { total: allData.length, expiring_soon: calculateExpiringSoon(allData), expired: calculateExpired(allData) }
  } catch (err) { console.error('统计加载失败:', err) }
}

const calculateExpiringSoon = (list) => list.filter(item => {
  if (!item.warranty_expire) return false
  const daysLeft = Math.ceil((new Date(item.warranty_expire) - new Date()) / (1000 * 3600 * 24))
  return daysLeft > 0 && daysLeft <= 90
}).length

const calculateExpired = (list) => list.filter(item => {
  if (!item.warranty_expire) return false
  const expireDate = new Date(item.warranty_expire); const today = new Date()
  today.setHours(0,0,0,0); expireDate.setHours(0,0,0,0)
  return expireDate < today
}).length

const isExpiring = (dateStr) => {
  if (!dateStr) return false
  const daysLeft = Math.ceil((new Date(dateStr) - Date.now()) / (1000 * 3600 * 24))
  return daysLeft > 0 && daysLeft <= 30
}

// ===== 工具函数 =====
const filterByEnv = (env) => { activeEnvFilter.value = env; currentPage.value = 1; fetchData() }
const filterByWarranty = (status) => { activeWarrantyFilter.value = status; currentPage.value = 1; fetchData() }
const getEnvLabel = (value) => environmentOptions.find(e => e.value === value)?.label || value || '-'
const envTagType = (envCode) => ({ prod: 'danger', stg: 'warning', dr: 'warning', uat: 'primary', test: 'primary', dev: 'success', other: 'info' }[envCode] || 'info')

const formatDateShort = (cellValue) => {
  if (!cellValue) return '-'
  try { const d = new Date(cellValue); if (isNaN(d.getTime())) return cellValue; return d.toISOString().split('T')[0] } catch { return cellValue }
}
const formatDateTime = (cellValue) => {
  if (!cellValue) return '-'
  try {
    const d = new Date(cellValue)
    if (isNaN(d.getTime())) return cellValue
    return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch { return cellValue }
}

// 格式化URL，确保有协议前缀
const formatUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  // 默认添加 https://
  return `https://${url}`
}

const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleSizeChange = (val) => { pageSize.value = val; fetchData() }
const handleCurrentChange = (val) => { currentPage.value = val; fetchData() }

// ===== 弹窗控制 =====
const openCreateDialog = () => {
  dialogMode.value = 'create'
  currentFormData.value = getDefaultItem()
  formDialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

const openEditDialog = (item) => {
  dialogMode.value = 'edit'
  currentFormData.value = { ...item }
  formDialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

// 详情弹窗 - 重置密码可见性
const openDetailDialog = async (item) => {
  dialogMode.value = 'detail'
  // 重置密码可见性
  passwordVisibility.value = {
    virtualization: false,
    management: false,
    bios: false
  }
  formLoading.value = true
  detailDialogVisible.value = true

  try {
    // 如果有详情接口，可以在这里调用
    // const res = await getProjectBareMetal(item.id)
    // currentFormData.value = res.data || res
    currentFormData.value = { ...item }
  } catch (err) {
    console.error('加载详情失败:', err)
    ElMessage.error('加载详情失败')
    currentFormData.value = { ...item }
  } finally {
    formLoading.value = false
  }
}

const editFromDetail = () => {
  detailDialogVisible.value = false
  dialogMode.value = 'edit'
  formDialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

const save = () => {
  if (!formRef.value) return
  formRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.warning('请填写所有必填项')
      return
    }
    formLoading.value = true
    try {
      if (currentFormData.value.id) {
        await updateProjectBareMetal(currentFormData.value.id, currentFormData.value)
        ElMessage.success('更新成功')
      } else {
        await createProjectBareMetal(currentFormData.value)
        ElMessage.success('创建成功')
      }
      formDialogVisible.value = false
      fetchData()
    } catch (err) {
      const errData = err?.response?.data
      if (errData && typeof errData === 'object') {
        const msgs = Object.entries(errData).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join('\n')
        ElMessage.error(msgs || '操作失败')
      } else {
        ElMessage.error(errData?.detail || '操作失败')
      }
    } finally {
      formLoading.value = false
    }
  })
}

// ===== 密码显示控制 =====
const togglePasswordVisibility = (type) => {
  passwordVisibility.value[type] = !passwordVisibility.value[type]
}

// 复制密码
const copyPassword = (password) => {
  if (!password) {
    ElMessage.warning('密码为空')
    return
  }
  copyToClipboard(password)
}

const copyToClipboard = (text) => {
  if (!text) {
    ElMessage.warning('内容为空')
    return
  }

  // 优先使用现代 Clipboard API
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      ElMessage.success('已复制到剪贴板')
    }).catch((err) => {
      console.log('Clipboard API 失败:', err)
      fallbackCopy(text)
    })
  } else {
    fallbackCopy(text)
  }
}

// 降级复制方案（兼容 HTTP 和老旧浏览器）
const fallbackCopy = (text) => {
  try {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0;pointer-events:none;'
    document.body.appendChild(textarea)

    // 兼容移动端的选择
    if (navigator.userAgent.match(/ipad|iphone/i)) {
      const range = document.createRange()
      range.selectNodeContents(textarea)

      const selection = window.getSelection()
      selection.removeAllRanges()
      selection.addRange(range)
      textarea.setSelectionRange(0, 999999)
    } else {
      textarea.select()
    }

    const successful = document.execCommand('copy')
    document.body.removeChild(textarea)

    if (successful) {
      ElMessage.success('已复制到剪贴板')
    } else {
      throw new Error('execCommand failed')
    }
  } catch (err) {
    console.error('复制失败:', err)
    ElMessage.error('复制失败，请手动选中复制')
  }
}

// ===== 删除 =====
const deleteItem = (item) => { deleteItemData.value = { ...item }; deleteDialogVisible.value = true }
const confirmDelete = async () => {
  try { await deleteProjectBareMetal(deleteItemData.value.id); ElMessage.success('删除成功'); deleteDialogVisible.value = false; fetchData() }
  catch (err) { ElMessage.error('删除失败') }
}

onMounted(() => { fetchData() })
</script>

<style scoped>
.baremetal-container { padding: 20px; background-color: #f5f7fa; }
.search-bar { display: flex; align-items: center; margin-bottom: 10px; }

/* 环境卡片 */
.env-stat-row { display: flex; gap: 12px; margin: 16px 0; flex-wrap: wrap; }
.env-stat-card { display: flex; align-items: center; gap: 8px; padding: 12px 18px; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); cursor: pointer; transition: all 0.25s; border: 2px solid transparent; user-select: none; }
.env-stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.env-stat-card.active { border-color: #409eff; background: #ecf5ff; }
.env-icon { font-size: 20px; color: #409eff; } .env-icon.prod { color: #f56c6c; } .env-icon.stg { color: #e6a23c; } .env-icon.uat { color: #409eff; } .env-icon.test { color: #409eff; } .env-icon.dev { color: #67c23a; } .env-icon.other { color: #909399; }
.env-label { font-size: 13px; color: #606266; }
.env-count { font-size: 20px; font-weight: bold; color: #409eff; margin-left: 4px; } .env-count.prod { color: #f56c6c; } .env-count.stg { color: #e6a23c; } .env-count.uat { color: #409eff; } .env-count.test { color: #409eff; } .env-count.dev { color: #67c23a; } .env-count.other { color: #909399; }

/* 保修状态筛选标签 */
.warranty-filter-row { display: flex; gap: 12px; margin: 16px 0; flex-wrap: wrap; }
.warranty-filter-card { display: flex; align-items: center; gap: 8px; padding: 12px 18px; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); cursor: pointer; transition: all 0.25s; border: 2px solid transparent; user-select: none; }
.warranty-filter-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.warranty-filter-card.active { border-color: #409eff; background: #ecf5ff; }
.warranty-filter-card.active.warning { border-color: #e6a23c; background: #fdf6ec; }
.warranty-filter-card.active.danger { border-color: #f56c6c; background: #fef0f0; }
.warranty-icon { font-size: 20px; color: #409eff; }
.warranty-filter-card.warning .warranty-icon { color: #e6a23c; }
.warranty-filter-card.danger .warranty-icon { color: #f56c6c; }
.warranty-label { font-size: 13px; color: #606266; }
.warranty-count { font-size: 20px; font-weight: bold; color: #409eff; margin-left: 4px; }
.warranty-count.warning { color: #e6a23c; }
.warranty-count.danger { color: #f56c6c; }

/* 统计卡片 */
.card-icon { font-size: 20px; margin-right: 8px; }
.stat-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1); transition: all 0.3s; }
.stat-card:hover { transform: translateY(-5px); box-shadow: 0 4px 16px 0 rgba(0,0,0,0.15); }
.card-header { display: flex; align-items: center; margin-bottom: 10px; color: #606266; }
.card-body { text-align: center; }
.display-4 { font-size: 28px; font-weight: bold; color: #409EFF; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }

/* 表格卡片 */
.table-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1); }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; }

/* 自定义弹窗样式 */
:deep(.custom-dialog) {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}
:deep(.custom-dialog .el-dialog__header) {
  margin: 0;
  padding: 16px 20px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e1e4e8;
}
:deep(.custom-dialog .el-dialog__title) {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}
:deep(.custom-dialog .el-dialog__body) {
  padding: 0;
}
:deep(.custom-dialog .el-dialog__footer) {
  padding: 12px 20px;
  border-top: 1px solid #e1e4e8;
  background-color: #fafbfc;
}

/* 详情弹窗特殊样式 */
.detail-dialog :deep(.el-dialog__body) {
  padding: 0;
  background-color: #f0f2f5;
}

/* 统一表单/详情容器 */
.form-container, .detail-container {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
  background-color: #f0f2f5;
  scrollbar-width: thin;
}
.form-container::-webkit-scrollbar, .detail-container::-webkit-scrollbar {
  width: 6px;
}
.form-container::-webkit-scrollbar-thumb, .detail-container::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

/* 分块样式 */
.group-block {
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  margin-bottom: 16px;
  border: 1px solid #ebeef5;
  overflow: hidden;
}
.group-header {
  padding: 12px 16px;
  background-color: #fafafa;
  border-bottom: 1px solid #ebeef5;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
}
.group-header::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 14px;
  background-color: #409eff;
  margin-right: 8px;
  border-radius: 2px;
}
.group-content {
  padding: 20px;
}

/* 详情模式下 descriptions 样式优化 */
:deep(.el-descriptions) {
  background: #fff;
}
:deep(.el-descriptions__label) {
  width: 120px;
  min-width: 120px;
  background-color: #f5f7fa;
  font-weight: 500;
  color: #606266;
}
:deep(.el-descriptions__content) {
  min-width: 200px;
}

/* 可点击链接样式 */
.link-address {
  color: #409eff;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  word-break: break-all;
}
.link-address:hover {
  color: #66b1ff;
  text-decoration: underline;
}
.link-address .el-icon {
  font-size: 14px;
}

/* 密码行内显示样式 */
.password-field-inline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 12px;
}
.password-text {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #909399;
  letter-spacing: 2px;
  user-select: all;
  flex: 1;
  word-break: break-all;
}
.password-text.is-visible {
  color: #303133;
  letter-spacing: 0;
  background-color: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}
.password-actions-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.password-actions-inline .action-btn {
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  color: #909399;
}
.password-actions-inline .action-btn:hover {
  color: #409eff;
  background-color: #ecf5ff;
}
.password-actions-inline .action-btn.copy-btn:hover {
  color: #67c23a;
  background-color: #f0f9eb;
}
</style>
