<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: { type: Number, required: true },
  skip: { type: Number, required: true },
  limit: { type: Number, required: true },
})

const emit = defineEmits(['change'])

const currentPage = computed(() => Math.floor(props.skip / props.limit) + 1)
const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.limit)))
const fromItem = computed(() => (props.total === 0 ? 0 : props.skip + 1))
const toItem = computed(() => Math.min(props.skip + props.limit, props.total))

function goTo(page) {
  const safePage = Math.max(1, Math.min(totalPages.value, page))
  emit('change', (safePage - 1) * props.limit)
}
</script>

<template>
  <div v-if="total > 0" class="pagination">
    <span>Mostrando {{ fromItem }}–{{ toItem }} de {{ total }}</span>
    <div class="pagination-controls">
      <button
        type="button"
        class="btn btn-secondary btn-sm"
        :disabled="currentPage <= 1"
        @click="goTo(currentPage - 1)"
      >
        Anterior
      </button>
      <span>Página {{ currentPage }} de {{ totalPages }}</span>
      <button
        type="button"
        class="btn btn-secondary btn-sm"
        :disabled="currentPage >= totalPages"
        @click="goTo(currentPage + 1)"
      >
        Siguiente
      </button>
    </div>
  </div>
</template>
