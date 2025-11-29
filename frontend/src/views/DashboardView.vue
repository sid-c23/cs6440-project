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

            <button class="exportRecords" @click="exportRecords">
                Send migraine history to my doctor
            </button>
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
              <button 
                :class="{ active: currTab === 'migraines' }"
                @click="currTab = 'migraines'"
              >Migraines</button>
              <button 
                :class="{ active: currTab === 'triggers' }"
                @click="currTab = 'triggers'"
              >Triggers</button>
              <button 
                :class="{ active: currTab === 'preventions' }"
                @click="currTab = 'preventions'"
              >Preventions</button>
            </div>
          <div class="chart-placeholder">

              <!-- SWITCH BETWEEN VIEWS -->
              <div v-show="currTab === 'migraines'">
                <h3>Migraines This Week</h3>
                <canvas id="migraineChart"></canvas>
              </div>

              <div v-if="currTab === 'triggers'">
                <h3>Trigger Summary</h3>

                <h4>Sleep</h4>
                <ul>
                  <li v-for="s in weeklyStats.sleep" :key="s.date">
                    {{ new Date(s.date).toLocaleDateString() }} — Slept {{ s.hours }} hrs
                  </li>
                </ul>

                <h4>Stress</h4>
                <ul>
                  <li v-for="s in weeklyStats.stress" :key="s.date">
                    {{ new Date(s.date).toLocaleDateString() }} — Stress {{ s.rating }}/5
                  </li>
                </ul>
              </div>

              <div v-if="currTab === 'preventions'">
                <h3>Preventions</h3>

                <h4>Exercise</h4>
                <ul>
                  <li v-for="e in weeklyStats.exercise" :key="e.date">
                    {{ new Date(e.date).toLocaleDateString() }} — Exercised ✔️
                  </li>
                </ul>

                <h4>Medication</h4>
                <ul>
                  <li v-for="m in weeklyStats.medication" :key="m.date">
                    {{ new Date(m.date).toLocaleDateString() }} — Medication Taken 💊
                  </li>
                </ul>
              </div>
            </div>
        </div>
      </section>

      <!-- Daily Record + This Week (Tracker) -->
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
              @click="submissionButton"
            >
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

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import Chart from "chart.js/auto";

const route = useRoute()
const userId = route.params.userId
const user = ref(null)
const migraines = ref([])

//watch(migraines, () => {
  //loadWeeklyInsights() 
  //displayStats()
//})

const triggers = ref([])
const loading = ref(true)
const error = ref(null)

function submissionButton() {
  if (idx.value < questions.value.length - 1) {
    nextQuestion();
  } else {
    submitDailyRecord();
  }
}

async function submitDailyRecord() {
  try {
    const a = answers.value; // shortcut

    if (a[1] === "Yes") {
      await fetch(`/api/event?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          system: "LOINC",
          code: "LA15141-7",
          event_type: "migraine",
          severity: parseInt(a[3][0]), // “3: moderately” → 3
          description: `Migraine at ${a.migraine_datetime}`
        }),
      });
    }

    if (a[4]) {
      await fetch(`/api/event?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          system: "ICD-10",
          code: "Z73.3",
          event_type: "stress",
          severity: parseInt(a[4][0]),
          description: "Daily stress rating"
        }),
      });
    }

    if (a[5]) {
      await fetch(`/api/event?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          system: "ICD-10",
          code: "Y93.84",
          event_type: "sleep",
          numerical_value: parseInt(a[5]),
          numerical_unit: "hours",
          description: "Hours slept"
        }),
      });
    }

    if (a[6]) {
      await fetch(`/api/event?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          system: "ICD-10",
          code: "Y93.G1",
          event_type: "meals",
          numerical_value: parseInt(a[6]),
          numerical_unit: "number",
          description: "Meals eaten"
        }),
      });
    }

    alert("Your daily record has been saved!");
  } catch (err) {
    console.error(err);
    alert("Error saving your daily migraine record. Please try again.");
  }
}

const exportRecords = async () => {
  try {
    const res = await fetch(`/api/fhir/export/${userId}`, {
      method: "POST"
    });

    if (!res.ok) throw new Error("Export to server failed");

    const data = await res.json();

    alert(`Exported to HAPI FHIR demo serve. Patient ID: ${data.patient_id}`);
  } catch (err) {
    console.error(err);
    alert("Error exporting to HAPI FHIR.");
  }
};


async function activateDashboard() {
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

  loadWeeklyInsights()
  displayStats()
}

onMounted(() => activateDashboard())

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

// WEEKLY ANALYTICS SECTION - BAR GRAPHS
const currTab = ref("migraines");

//watch(currTab, () => {
  //displayStats();
//});

const weeklyStats = ref({
  migraines: {
      total: 0,
      avg_intensity: 0,
      morning: 0,
      afternoon: 0,
      night: 0
    },

    sleep: [],
    stress: [],
    exercise: [],
    medication: []
});

async function loadWeeklyInsights() {
  weeklyStats.value = {
    migraines: {
      total: 2,
      avg_intensity: 3.5,
      morning: 1,
      afternoon: 1,
      night: 0
    },
    sleep: [
      { date: "2025-01-27", hours: 6 },
      { date: "2025-01-28", hours: 7 }
    ],
    stress: [
      { date: "2025-01-27", rating: 4 }
    ],
    exercise: [
      { date: "2025-01-27", value: true }
    ],
    medication: []
  }
}


let migraineChart = null;
function displayStats() {

  if (currTab.value !== "migraines") return;

  const el = document.getElementById("migraineChart");
  if (!el) return;


  const migraineData = weeklyStats.value.migraines || {};
  const count = migraineData.total || 0;
  const avgIntensity = migraineData.avg_intensity || 0;


  migraineChart = new Chart(el, {
    type: "bar",
    data: {
      labels: ["Total Migraines", "Avg Intensity"],
      datasets: [
        {
          label: "Migraine Stats",
          data: [count, avgIntensity],
          backgroundColor: ["#008080", "#4db6ac"]
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      }
    }
  });
}
</script>


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
  padding: 1rem;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  min-height: 220px; 
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
.exportRecords {
  margin-top: 1rem;
  background-color: #ffffff;
  color: #008080;
  border: 2px solid #ffffff;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  width: 100%;
  transition: 0.2s ease-in-out;
}

.exportRecords:hover {
  background-color: #b2dfdb;
  border-color: #b2dfdb;
  color: #004d40;
}

.tabs button.active {
  background: #008080; 
  color: white;
  border: 2px solid #00695c;
}

.weekly-insights h3 {
  text-align: center;
  margin-top: 0.5rem;
  margin-bottom: 1rem;
  font-size: 1.4rem;
  color: #004d40;
}

#migraineChart {
  margin-top: 0.5rem;
  max-height: 250px;
}

</style>


