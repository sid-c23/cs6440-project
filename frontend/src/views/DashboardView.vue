<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const userId = route.params.userId
const user: any = ref(null)
const migraines = ref([])
const triggers = ref([])
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    const resUser = await fetch(`/api/users/${userId}`)
    if (!resUser.ok) throw new Error('Failed to load user')
    user.value = await resUser.json()

    const resMigraines = await fetch(`/api/migraines?user_id=${userId}`)
    if (resMigraines.ok) migraines.value = await resMigraines.json()

    const resTriggers = await fetch(`/api/triggers?user_id=${userId}`)
    if (resTriggers.ok) triggers.value = await resTriggers.json()

  } catch (err) {
    console.error(err)
    error.value = 'Error loading dashboard data.'
  } finally {
    loading.value = false
  }
})

const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const migraineDays = ref([true, true, false, true, false, false, false])
function toggleDay(index) {
  migraineDays.value[index] = !migraineDays.value[index]
}
</script>

<template>
  <div class="dashboard">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="logo">
        <span class="icon">💊</span>
        <span class="title">MyMigraine<br />Management</span>
      </div>

      <template v-if="user">
        <div class="user-info">
            <div class="avatar">👤</div>
            <div class="details">
                <p class="name">{{ user.name }}</p>
                <!-- replace with email -->
                <p class="email">{{ user.id }}</p>
                <!-- replace with dob -->
                <p class="dob">Member Since: {{ new Date(user.creation_timestamp).toLocaleDateString() }}</p>
            </div>
        </div>
      </template>

      <template v-else-if="loading">
        <div>Loading user dashboard...</div>
      </template>
      <template v-else-if="error">
        <div>{{ error }}</div>
      </template>
    </aside>

    <!-- Main content -->
    <main class="content">
      <!-- Weekly Tip -->
      <section class="weekly-tip">
        <p>
          weekly insight here.
          <strong>weekly tip here!</strong>
        </p>
      </section>

      <!-- Weekly Insights -->
      <section class="weekly-insights">
        <h2>Your Weekly Insights</h2>
        <div class="insights-box">
          <div class="tabs">
            <button>Migraines</button>
            <button>Triggers</button>
            <button>Preventions</button>
          </div>
          <div class="chart-placeholder">[Chart Placeholder]</div>
        </div>
      </section>

      <!-- Daily Record + This Week -->
      <section class="daily-record">
        <div class="record-box">
          <h3>Your Daily Record</h3>
          <div v-if="questions.length">
            <p>{{ questions[idx].text }}</p>

            <div v-if="questions[idx].type == 'radio'">
              <label
                v-for="option in questions[idx].options"
                :key="option"
              >
                <input
                  type="radio"
                  :name="'question-' + idx"
                  :value="option"
                  v-model="answers[idx]"
                />
                {{ option }}
              </label>
            </div>

            <div v-else-if="questions[idx].type === 'text'">
              <input
                type="text"
                v-model="answers[idx]"
                :placeholder="questions[idx].placeholder"
              />
            </div>

            <div v-else-if="questions[idx].type === 'number'">
              <input
                type="number"
                v-model="answers[idx]"
                :placeholder="questions[idx].placeholder"
              />
            </div>

            <div v-else-if="questions[idx].type === 'date'">
              <input
                type="date"
                v-model="answers[idx]"
                :placeholder="questions[idx].placeholder"
              />
            </div>

            <div v-else-if="questions[idx].type === 'time'">
              <input
                type="time"
                v-model="answers[idx]"
                :placeholder="questions[idx].placeholder"
              />
            </div>

            <button
              class="next-btn"
              :disabled="!answers[idx]"
              @click="nextQuestion">
              {{ idx < questions.length - 1 ? 'Next' : 'Submit'}}
            </button>
          </div>
        </div>


        <!--
        < add back in later with functionality > 
        <div class="week-box">
          <h3>This Week</h3>
          <ul>
            <li v-for="(day, index) in weekDays" :key="day" @click="toggleDay(index)" :class="{ selected: migraineDays[index] }" role="checkbox" :aria-checked="migraineDays[index]">
              {{ day }} <span class="bubble">{{ migraineDays[index] ? '●' : '○' }}</span>
            </li>
          </ul>
        </div>
        -->
      </section>
    </main>
  </div>
</template>

<<<<<<< HEAD
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const userId = route.params.userId
const user = ref(null)
const migraines = ref([])
const triggers = ref([])
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    const resUser = await fetch(`http://127.0.0.1:8000/api/users/${userId}`)
    if (!resUser.ok) throw new Error('Failed to load user')
    user.value = await resUser.json()

    const resMigraines = await fetch(`http://127.0.0.1:8000/api/migraines?user_id=${userId}`)
    if (resMigraines.ok) migraines.value = await resMigraines.json()

    const resTriggers = await fetch(`http://127.0.0.1:8000/api/triggers?user_id=${userId}`)
    if (resTriggers.ok) triggers.value = await resTriggers.json()

  } catch (err) {
    console.error(err)
    error.value = 'Error loading dashboard data.'
  } finally {
    loading.value = false
  }
})

const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const migraineDays = ref([false, false, false, false, false, false, false])
function toggleDay(index) {
  migraineDays.value[index] = !migraineDays.value[index]
}

//daily record box questions - to be recorded under user observations
const questions = ref([
    { text: 'Please select the date you are logging', type: 'date'},
    { text: 'Did you experience a migraine today?', type: 'radio', options: ['Yes', 'No']},
    { text: 'What time did the migraine occur?', type: 'time'},
    { text: 'How would you rate your migraine intensity?', type: 'radio', options: ['1: Not at all severe', '2: Somewhat severe', '3: Moderately severe', '4: Very severe', '5: Extremely severe']},
    { text: 'How stressed were you today?', type: 'radio', options: ['1: Not at all stressed', '2: Somewhat stressed', '3: Moderately stressed', '4: Very stressed', '5: Extremely stressed']},
    { text: 'How many hours did you sleep?', type: 'number', placeholder: 'Enter number of hours'},
    { text: 'How many meals did you eat today?', type: 'number', placeholder: 'Enter number of meals'},
    { text: 'Did you exercise today?' , type: 'radio', options: ['Yes', 'No']},
    { text: 'Did you take any remedial medication today? Eg: Aspirin, Excedrin, Prescribed Medications', type: 'radio', options: ['Yes', 'No']}  
])

const today = new Date().toISOString().split('T')[0]
const answers = ref({ 0: today })
const idx = ref(0)

function nextQuestion() {
    //store migraine time as datetime instead of time (easier for analytics)
    if (
        idx.value > 0 &&
        questions.value[idx.value].type === 'time' &&
        questions.value[idx.value - 1].type === 'date'
    ) {
        const date = answers.value[idx.value - 1]
        const time = answers.value[idx.value]
        if (date && time) {
            const dt = `${date}T${time}`
            answers.value['migraine_datetime'] = dt
            console.log('Migraine datetime:', dt)
        }
    }
    if (idx.value < questions.value.length - 1) {
        idx.value++
    } else {
        console.log('All answers:', answers.value)
        alert('Thanks for completing your daily record!')
        idx.value = 0 // option to add response for another day
        answers.value = { 0: new Date().toISOString().split('T')[0]}  //resets questions instead of keeping answers
    }
}
</script>

=======
>>>>>>> 2a21e3af61a5a90bcd26df68721b4c7e1d34bc2c
<style scoped>
.dashboard {
  display: flex;
  font-family: Arial, sans-serif;
  height: 100vh;
}

/* Sidebar */
.sidebar {
  width: 250px;
  background-color: #008080; /* teal */
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem;
}

.logo {
  text-align: center;
  margin-bottom: 2rem;
}
.logo .icon {
  font-size: 1.5rem;
}
.logo .title {
  font-weight: bold;
  font-size: 1.1rem;
}

.user-info {
  text-align: center;
}
.avatar {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}
.details p {
  margin: 0.2rem 0;
  font-size: 0.9rem;
}

/* Content */
.content {
  flex: 1;
  background-color: #f9fafb;
  padding: 2rem;
  overflow-y: auto;
  color: #008080; /* teal text */
}

.weekly-tip {
  background: #e0f2f1; /* lighter teal background */
  border: 1px solid #4db6ac;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.weekly-insights {
  margin-bottom: 2rem;
}
.insights-box {
  background: white;
  border: 1px solid #b2dfdb;
  border-radius: 8px;
  padding: 1rem;
}
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.tabs button {
  flex: 1;
  background: #b2dfdb;
  border: none;
  padding: 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  color: #004d40;
  font-weight: 600;
}
.chart-placeholder {
  background: #e0f2f1;
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #004d40;
}

/* Daily Record + Week */
.daily-record {
  display: flex;
  gap: 2rem;
}

.record-box, .week-box {
  background: white;
  border: 1px solid #b2dfdb;
  border-radius: 8px;
  padding: 1rem;
  flex: 1;
  color: #004d40;
}

.next-btn {
  background: #008080;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 1rem;
}
.week-box ul {
  list-style: none;
  padding: 0;
}
.week-box li {
  margin: 0.3rem 0;
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #004d40;
}
.week-box li.selected {
  color: #00695c;
  font-weight: 700;
}
.bubble {
  font-size: 1.2rem;
  user-select: none;
}
.record-box label {
  display: block;
  margin: 0.3rem 0;
  cursor: pointer;
}
.record-box label input {
  margin-right: 0.4rem;
}
</style>


