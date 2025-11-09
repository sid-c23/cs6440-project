<script setup lang="ts">
import { RouterView } from 'vue-router';
import { ref, onMounted } from 'vue';
import axios from 'axios';

const users = ref([]);

onMounted(async () => {
  console.log("hi there")
  const res = await axios.get("/api/users");
  users.value = res.data
  console.log(res);
})

</script>

<template>
  {{ users }}
  <RouterView />
</template>

<style scoped></style>
