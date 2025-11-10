<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ref, onMounted } from 'vue'


// updating to pull users from backend
//const users = [
//  { id: 1, name: 'First Name Last Name', email: 'email@example.com', dob: '01/01/0000' },
//  { id: 2, name: 'First Name Last Name', email: 'email@example.com', dob: '01/01/0000' },
//  { id: 3, name: 'First Name Last Name', email: 'email@example.com', dob: '01/01/0000' }
// ]

const users: any = ref([])

onMounted(async () => {
  try {
    const response = await fetch('/api/users')
    if (!response.ok) throw new Error('failure getting users from backend')
    const patients = await response.json()
    users.value = patients.sort((a, b) => a.name.localeCompare(b.name))
  } catch (error) {
    console.error('user load error:', error)
  }
})

const router = useRouter()

function goToDashboard(userId) {
  router.push(`/dashboard/${userId}`)
}
</script>

<template>
  <div class="users-page">
    <h1>Users</h1>
    <ul class="users-list">
      <li
        v-for="user in users"
        :key="user.id"
        @click="goToDashboard(user.id)"
        class="user-item"
        role="button"
        tabindex="0"
        @keyup.enter="goToDashboard(user.id)"
      >
        <p class="user-name">{{ user.name }}</p>

        <!-- add dob and email in later once in pt jsons -->
        <!-- <p class="user-email">{{ user.email }}</p> -->
        <!-- <p class="user-dob">DOB: {{ user.dob }}</p> -->

        <p class="user-dob">Patient Creation Timestamp: {{ new Date(user.creation_timestamp).toLocaleString() }}</p>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.users-page {
  padding: 2rem;
  font-family: Arial, sans-serif;
  color: #004d40;
}

.users-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.user-item {
  background: #e0f2f1;
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.user-item:hover,
.user-item:focus {
  background: #b2dfdb;
  outline: none;
}

.user-name {
  font-weight: bold;
  font-size: 1.1rem;
  margin: 0 0 0.2rem 0;
}

.user-email,
.user-dob {
  margin: 0;
  font-size: 0.9rem;
}
</style>

