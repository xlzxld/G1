<template>
  <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-5 shadow-lg flex flex-col h-full">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-semibold flex items-center gap-2">
        <el-icon><Box /></el-icon>订单用料与零配件
      </h2>
      <el-button
        v-if="!isCompleted"
        type="primary"
        size="small"
        plain
        @click="openAddModal"
      >
        <el-icon><Plus /></el-icon>&nbsp;分配用料
      </el-button>
      <el-tag v-else type="success" size="small" effect="dark" class="flex items-center gap-0.5">
        <el-icon><SuccessFilled /></el-icon>库存已联动扣减
      </el-tag>
    </div>

    <!-- Materials list -->
    <div class="mt-2 flex-1">
      <el-table
        :data="materials"
        border
        stripe
        size="small"
        empty-text="暂无用料数据"
        class="w-full"
        max-height="220"
      >
        <el-table-column prop="item_name" label="配件名称" min-width="120" show-overflow-tooltip />
        <el-table-column prop="spec" label="规格" min-width="100" show-overflow-tooltip />
        <el-table-column prop="quantity" label="数量" width="80" align="center">
          <template #default="{ row }">
            <span class="font-semibold text-slate-800 dark:text-slate-200">
              {{ row.quantity }}
            </span>
            <span class="text-[10px] text-slate-400 dark:text-slate-500 ml-0.5">{{ row.unit }}</span>
          </template>
        </el-table-column>
        <el-table-column v-if="!isCompleted" label="操作" width="60" align="center">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              icon="Delete"
              circle
              plain
              @click="confirmDelete(row)"
            />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Summary / Info -->
    <div class="mt-4 pt-3 border-t border-slate-100 dark:border-industrial-border text-xs text-slate-400 dark:text-slate-500">
      <p v-if="!isCompleted">
        * 分配用料将预留库存，订单完成（完工）时会自动在系统中扣除这些配件的总库存。
      </p>
      <p v-else class="text-green-500 dark:text-green-400">
        已成功释放对应预留并扣减了零配件物理总库存。
      </p>
    </div>

    <!-- Add Material Modal -->
    <el-dialog v-model="dialogVisible" title="分配零配件用料" width="440px" append-to-body>
      <el-form label-width="80px" class="mt-2">
        <el-form-item label="选择零配件">
          <el-select
            v-model="form.item_id"
            placeholder="请选择库存零配件"
            class="w-full"
            filterable
            @change="handleItemChange"
          >
            <el-option
              v-for="item in inventoryItems"
              :key="item.id"
              :label="`${item.name} (${item.spec || '无规格'})`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <!-- Display stock status when item is selected -->
        <div v-if="selectedItem" class="bg-slate-50 dark:bg-industrial-700/50 p-3 rounded-lg mb-4 ml-[80px] text-xs">
          <div class="flex justify-between mb-1">
            <span class="text-slate-400">物理总库存:</span>
            <span class="font-medium text-slate-700 dark:text-slate-200">{{ selectedItem.total }} {{ selectedItem.unit }}</span>
          </div>
          <div class="flex justify-between mb-1">
            <span class="text-slate-400">已预留库存:</span>
            <span class="font-medium text-slate-700 dark:text-slate-200">{{ selectedItem.reserved }} {{ selectedItem.unit }}</span>
          </div>
          <div class="flex justify-between border-t border-slate-200 dark:border-industrial-border pt-1 font-semibold">
            <span class="text-blue-500">当前可用量:</span>
            <span class="text-blue-600 dark:text-blue-400">{{ availableQty }} {{ selectedItem.unit }}</span>
          </div>
        </div>

        <el-form-item label="用料数量">
          <el-input-number
            v-model="form.quantity"
            :min="1"
            :max="availableQty > 0 ? availableQty : 1"
            class="w-full"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="saving"
          :disabled="!form.item_id || form.quantity <= 0 || availableQty <= 0"
          @click="submitAdd"
        >
          确定分配
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Box, Plus, SuccessFilled } from '@element-plus/icons-vue';
import api from '../api/index.js';

const props = defineProps({
  orderId: { type: Number, required: true },
  orderStatus: { type: String, required: true }
});

const materials = ref([]);
const inventoryItems = ref([]);
const dialogVisible = ref(false);
const saving = ref(false);

const form = ref({
  item_id: null,
  quantity: 1
});

const isCompleted = computed(() => props.orderStatus === 'completed');

// Load initial data
onMounted(() => {
  fetchMaterials();
  fetchInventory();
});

// Watch orderStatus change to refetch data
watch(() => props.orderStatus, () => {
  fetchMaterials();
});

async function fetchMaterials() {
  try {
    const res = await api.get(`/orders/${props.orderId}/materials`);
    materials.value = res.data;
  } catch (e) {
    console.error("加载用料失败", e);
  }
}

async function fetchInventory() {
  try {
    const res = await api.get('/inventory');
    inventoryItems.value = res.data;
  } catch (e) {
    console.error("加载库存零配件失败", e);
  }
}

const selectedItem = computed(() => {
  if (!form.value.item_id) return null;
  return inventoryItems.value.find(i => i.id === form.value.item_id) || null;
});

const availableQty = computed(() => {
  if (!selectedItem.value) return 0;
  return Math.max(0, selectedItem.value.total - selectedItem.value.reserved);
});

function handleItemChange() {
  form.value.quantity = 1;
}

function openAddModal() {
  form.value.item_id = null;
  form.value.quantity = 1;
  dialogVisible.value = true;
  // Refresh inventory data to get the latest quantities
  fetchInventory();
}

async function submitAdd() {
  saving.value = true;
  try {
    await api.post(`/orders/${props.orderId}/materials`, {
      item_id: form.value.item_id,
      quantity: form.value.quantity
    });
    ElMessage.success("用料分配成功");
    dialogVisible.value = false;
    await fetchMaterials();
    await fetchInventory();
  } catch (e) {
    const detail = e.response?.data?.detail || "用料分配失败";
    ElMessage.error(typeof detail === 'string' ? detail : "用料分配失败");
  } finally {
    saving.value = false;
  }
}

async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定移除零配件用料「${row.item_name}」？已预留的库存额度将自动返还。`,
      "确认移除",
      { type: "warning", confirmButtonClass: 'el-button--danger' }
    );
    await api.delete(`/orders/${props.orderId}/materials/${row.id}`);
    ElMessage.success("用料已移除，库存预留已回退");
    await fetchMaterials();
    await fetchInventory();
  } catch (e) {
    if (e === 'cancel' || e === 'close') return;
    const detail = e.response?.data?.detail || "移除失败";
    ElMessage.error(typeof detail === 'string' ? detail : "移除失败");
  }
}
</script>
