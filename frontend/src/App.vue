<script setup lang="ts">
import { RouterView } from 'vue-router';
import MyNavbar from './components/MyNavbar.vue';
import { ref, onMounted } from 'vue';
import axios from 'axios';

const users = ref([]);

onMounted(async () => {
  console.log("hi there")
  const res = await axios.get("http://localhost:8000/users");
  users.value = res.data
  console.log(res);
})

</script>

<template>
  <header>
      <!-- <nav>
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/about">About</RouterLink>
      </nav> -->
      <MyNavbar />
  </header>
  {{ users }}
  <RouterView />
</template>

<style scoped></style>
