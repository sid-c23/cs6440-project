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
                @click="() => { currTab = 'triggers'; displayTriggers(); }"
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
                <div class="statCharts">
                  <canvas id="migraineChart"></canvas>
                </div>
              </div>

              <div v-show="currTab === 'triggers'">
                <h3>Trigger Summary</h3>
                <div class="statCharts">
                  <canvas id="triggerChart"></canvas>
                </div>
              </div>
              <div v-if="currTab === 'preventions'">
                <h3>Weekly Prevention Tracker</h3>

                <table class="prevention-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Exercise</th>
                      <th>Medication</th>
                    </tr>
                  </thead>

                  <tbody>
                    <tr v-for="p in preventionWeek" :key="p.date">
                      <td>{{ new Date(p.date).toLocaleDateString() }}</td>
                      <td>{{ p.exercise ? "✔️" : "—" }}</td>
                      <td>{{ p.medication ? "✔️" : "—" }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
        </div>
      </section>

      <!-- Daily Record + This Week (Tracker) -->
      <section class="daily-record">
        <div class="record-box">
          <h3>Your Daily Record</h3>
          <div v-if="questions.length">
            <p v-if="!questions[idx].condition || questions[idx].condition()">
              {{ questions[idx].text }}
            </p>

            <div v-if="(!questions[idx].condition || questions[idx].condition()) && questions[idx].type == 'radio'">
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

            <div v-else-if="(!questions[idx].condition || questions[idx].condition()) && questions[idx].type === 'text'">
              <input
                type="text"
                v-model="answers[idx]"
                :placeholder="questions[idx].placeholder"
              />
            </div>

            <div v-else-if="(!questions[idx].condition || questions[idx].condition()) && questions[idx].type === 'number'">
              <input
                type="number"
                v-model="answers[idx]"
                :placeholder="questions[idx].placeholder"
              />
            </div>

            <div v-else-if="(!questions[idx].condition || questions[idx].condition()) && questions[idx].type === 'date'">
              <input
                type="date"
                v-model="answers[idx]"
                :placeholder="questions[idx].placeholder"
              />
            </div>

            <div v-else-if="(!questions[idx].condition || questions[idx].condition()) && questions[idx].type === 'time'">
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
import { ref, onMounted, watch, computed } from 'vue'
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
  if (idx.value === questions.value.length - 1) {
    submitDailyRecord();
  } else {
    nextQuestion();
  }
}

 async function submitDailyRecord() {
  try {
    const a = answers.value; // shortcut

    if (a[1] === "Yes") {
      const date = a[0];
      const time = a[2];
      if (date && time) {
        a.migraine_datetime = `${date}T${time}`;
      }
    }

    if (a[1] === "Yes") {
      await fetch(`/api/event?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          system: "LOINC",
          code: "LA15141-7",
          event_type: "migraine",
          severity: parseInt(a[3][0]), // “3: moderately” → 3
          description: `Migraine at ${a.migraine_datetime}`,
          event_timestamp: a.migraine_datetime
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
          description: "Daily stress rating",
          event_timestamp: `${a[0]}T00:00:00`
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
          description: "Hours slept",
          event_timestamp: `${a[0]}T00:00:00`
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
          description: "Meals eaten",
          event_timestamp: `${a[0]}T00:00:00`
        }),
      });
    }

    alert("Your daily record has been saved!");

    idx.value = 0
    answers.value = {
      0: new Date().toISOString().split("T")[0]
    }

  } catch (err) {
    console.error(err);
    alert("Error saving your daily migraine record. Please try again.");
  }
}


const exportRecords = async () => {
  try {
    const res = await fetch(`/api/export_patient_data_to_fhir/${userId}`, {
      method: "POST"
    });

    if (!res.ok) throw new Error("Export to server failed");

    const data = await res.json();

    alert(`Exported to HAPI FHIR demo server. Patient ID: ${data.patient.id}`);
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

    // adding conditional logic
    { text: 'What time did the migraine occur?', type: 'time', condition: () => answers.value[1] === "Yes" },
    { text: 'How would you rate your migraine intensity?', type: 'radio', 
      options: ['1: Not at all severe', '2: Somewhat severe', '3: Moderately severe', '4: Very severe', '5: Extremely severe'],
      condition: () => answers.value[1] === "Yes" },

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

    idx.value++;

    if (idx.value >= questions.value.length) {
      submitDailyRecord();
      return;
    }

    const quiz = questions.value[idx.value];
    if (quiz.condition && !quiz.condition()) {
      nextQuestion();
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
    meals: [], //forgot to add meals earlier, baseline should be 3 meals
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
      { date: "2025-11-27", hours: 6 },
      { date: "2025-11-28", hours: 7 }
    ],
    stress: [
      { date: "2025-11-27", rating: 4 }
    ],
    //NEW mock data for meals
    meals: [
      { date: "2025-11-27", count: 2 },
      { date: "2025-11-28", count: 3 }
    ],
    exercise: [
      { date: "2025-11-28", value: true } 
    ],
    medication: [
       { date: "2025-11-26", value: true }
    ]
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

let triggerChart = null;
function displayTriggers() {
  if (currTab.value !== "triggers") return;

  const el = document.getElementById("triggerChart");
  if (!el) return;
  if (triggerChart) return;

  const sleepHours = weeklyStats.value.sleep.map(s => s.hours);
  const stressLevels = weeklyStats.value.stress.map(s => s.rating);
  const mealCt = weeklyStats.value.meals.map(m => m.count);

  const labels = weeklyStats.value.sleep.map(s => 
    new Date(s.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric"
    })
  );

  triggerChart = new Chart(el, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Hours Slept",
          data: sleepHours,
          backgroundColor: "#4db6ac"
        },
        {
          label: "Stress Level",
          data: stressLevels,
          backgroundColor: "#ffab91"
        },
        {
          label: "Daily Meals",
          data: mealCt,
          backgroundColor: "#81d4fa"
        },
        {
          label: "Recommended Sleep",
          data: [7, 7],
          xAxisID: "baseline",
          spanGaps: true, 
          type: "line",
          borderColor: "#00695c",
          borderWidth: 2,
          pointRadius: 0,
          borderDash: [6, 6]
        },
        {
          label: "Recommended Daily Meals",
          data: [3, 3],
          xAxisID: "baseline",
          type: "line",
          borderColor: "#0277bd",
          borderWidth: 2,
          pointRadius: 0,
          borderDash: [6, 6]
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: { top: 5 }
      },
      plugins: {
        legend: { 
          display: true,
          position: "top",
          align: "start",
          labels: {
            usePointStyle: true,
            padding: 12,
            font: { size: 12 }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { font: { size: 12} }
        },
        x: {
          ticks: { font: { size: 12 } }
        },
        baseline: {
          type: "category",
          labels,
          display: false
        }
      }
    }
  });
}

// I'm just going to do a grid for preventions rn unless we decide otherwise

const preventionWeek = computed(() => {
  const today = new Date();
  const day = today.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  const monday = new Date(today);
  monday.setDate(today.getDate() + diff);

  const week = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);

    const iso = d.toLocaleDateString("en-CA");

    week.push({
      date: iso,
      exercise: weeklyStats.value.exercise.some(e => e.date === iso),
      medication: weeklyStats.value.medication.some(m => m.date === iso)
    });
  }

  return week;
});


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
  min-height: 420px;
}

.statCharts {
  width: 100%;
  height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.statCharts canvas {
  width: 100%;
  height: 320px;
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

.prevention-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  background: white;
  border-radius: 6px;
  overflow: hidden;
}

.prevention-table th {
  background: #b2dfdb;
  color: #004d40;
  padding: 0.6rem;
  font-weight: 600;
  text-align: left;
}

.prevention-table td {
  padding: 0.6rem;
  border-bottom: 1px solid #e0f2f1;
  color: #004d40;
  font-size: 0.95rem;
}

.prevention-table tr:last-child td {
  border-bottom: none;
}

.prevention-table td:nth-child(2),
.prevention-table td:nth-child(3) {
  text-align: center;
  font-size: 1.2rem;
}

</style>
