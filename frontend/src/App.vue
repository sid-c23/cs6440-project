<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router';
import HelloWorld from './components/HelloWorld.vue';
import { ref, onMounted } from 'vue';
import axios from 'axios';

const users = ref([]);

onMounted(async () => {
  const res = await axios.get("http://localhost:8000/users");
  users.value = res.data
})

</script>

<template>
  <header>
      <!-- <nav>
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/about">About</RouterLink>
      </nav> -->
  {{ users }}
  </header>
    <div class="wrapper">
      <HelloWorld msg="This is the message" />
    </div>
  <RouterView />
</template>

<style scoped>
</style>
