<script setup lang="ts">
import { ref } from 'vue';
import Menubar from 'primevue/menubar';

const items = ref([
  {
    label: 'Users'
  }
]);
</script>
<template>
  <Menubar :model="items" />
</template>
