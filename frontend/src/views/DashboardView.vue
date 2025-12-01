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
            <button class="exportRecords" @click="viewFhirData">
                See my health record
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
        <p v-html="weeklyTip"></p>
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
          event_type: "meal",
          numerical_value: parseInt(a[6]),
          numerical_unit: "number",
          description: "Meals eaten",
          event_timestamp: `${a[0]}T00:00:00`
        }),
      });
    }

    if (a[7] === "Yes") {
      await fetch(`/api/event?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          system: "ICD-10",
          code: "Y93.A9",        // DOUBLE CHECK ON BACKEND
          event_type: "exercise",
          description: "Exercise performed",
          event_timestamp: `${a[0]}T00:00:00`
        }),
      });
    }

    if (a[8] === "Yes") {
      await fetch(`/api/event?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          system: "ICD-10",
          code: "Z79.899",        // DOUBLE
          event_type: "medication",
          description: "Took remedial medication",
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

    //const resTriggers = await fetch(`/api/triggers?user_id=${userId}`)
    //if (resTriggers.ok) triggers.value = await resTriggers.json()
    await getTriggerData();
    await getRollingMigraines(); 
    console.log("sleep grouped:", weeklyStats.value.sleep);
    console.log("stress grouped:", weeklyStats.value.stress);
    console.log("meals grouped:", weeklyStats.value.meals);

  } catch (err) {
    console.error(err)
    error.value = 'Error loading dashboard data.'
  } finally {
    loading.value = false
  }

  //loadWeeklyInsights()
  //displayStats()
}


const weeklyTip = ref("");
const weeklyInsight = ref([]);

async function getWeeklyTip() {
  const res = await fetch(
    `/api/action-items?user_id=${userId}&window_size=2&use_localtime=false&min_sleep_hours=7&min_meals_per_day=3&stress_severity_threshold=3`
  );
  if (!res.ok) return;

  const data = await res.json();

  weeklyInsight.value = data.action_items || [];

  if (!data.summary?.percent_changes) return;

  const pct = data.summary.percent_changes;

  const changes = [
    { key: "sleep", value: pct.sleep },
    { key: "meals", value: pct.meals },
    { key: "stress", value: pct.stress_severity }
  ];

  const mostChanged = changes.sort((a, b) => (b.value || 0) - (a.value || 0))[0];

  const item = weeklyInsight.value.find(i =>
    i.title.toLowerCase().includes(mostChanged.key)
  );

  if (!item) return;

  weeklyTip.value = `${item.reason} <strong>${item.title}!</strong>`;
}


onMounted(async () => {
  await activateDashboard();
  await getWeeklyTip();
});



async function getTriggerData() {
  try {
    const res = await fetch(`/api/triggers?user_id=${userId}`);
    if (!res.ok) throw new Error("Failed to fetch triggers");

    const data = await res.json();

    console.log("Fetched trigger data:", data);

    const sleep = [];
    const stress = [];
    const meals = [];
    const exercise = [];
    const medication = [];

    data.forEach(event => {
      const date = event.event_timestamp
        ? event.event_timestamp.split("T")[0]
        : null;

      if (event.event_type === "sleep") {
        sleep.push({ date, hours: event.numerical_value });
      }

      if (event.event_type === "stress") {
        stress.push({ date, rating: event.severity });
      }

      if (event.event_type === "meal" || event.event_type === "meals") {
        meals.push({ date, count: event.numerical_value });
      }

      if (event.event_type === "exercise") {
        exercise.push({ date });
      }

      if (event.event_type === "medication") {
        medication.push({ date });
      }
    });

    weeklyStats.value.sleep = sleep;
    weeklyStats.value.stress = stress;
    weeklyStats.value.meals = meals;
    weeklyStats.value.exercise = exercise;
    weeklyStats.value.medication = medication;

    return true;

  } catch (err) {
    console.error("Error parsing trigger data", err);
    return false;
  }
}



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
    sleep: weeklyStats.value.sleep,
    stress: weeklyStats.value.stress,
    meals: weeklyStats.value.meals,
    exercise: weeklyStats.value.exercise,
    medication: weeklyStats.value.medication
  };
}

async function getRollingMigraines() {
  try {
    const res = await fetch(
      `/api/weekly/rolling?user_id=${userId}&window_size=1&use_localtime=false`
    );

    if (!res.ok) {
      console.error("Rolling migraine API failed:", res.status);
      return;
    }

    const data = await res.json();

    //console.log("RAW rolling migraine data:", data);

    if (!Array.isArray(data) || data.length === 0) {
      console.warn("Rolling migraine API returned empty array");
      return;
    }

    const latest = data[data.length - 1];
    //console.log("Latest rolling migraine entry:", latest);

    //console.log("week_start_monday:", latest?.week_start_monday);
    //console.log("moving_average_migraine_events:", latest?.moving_average_migraine_events);
    //console.log("moving_average_migraine_severity:", latest?.moving_average_migraine_severity);

    // Update weeklyStats AFTER logging
    weeklyStats.value.migraines = {
      week: latest.week_start_monday,
      events: latest.moving_average_migraine_events,
      severity: latest.moving_average_migraine_severity
    };

    displayStats();

    //console.log("Updated weeklyStats.migraines:", weeklyStats.value.migraines);

  } catch (err) {
    console.error("Error in getRollingMigraines:", err);
  }
}


let migraineChart = null;

function displayStats() {
  if (currTab.value !== "migraines") return;

  const el = document.getElementById("migraineChart");
  if (!el) return;

  const m = weeklyStats.value.migraines;
  if (!m || !m.week) {
    console.warn("Migraine stats not ready");
    return;
  }

  if (migraineChart) {
    migraineChart.destroy();
    migraineChart = null;
  }

  migraineChart = new Chart(el, {
    type: "bar",
    data: {
      labels: ["Migraine Events", "Avg Intensity"],   // 👈 TWO LABELS ONLY
      datasets: [
        {
          label: "Migraine Stats",
          data: [m.events, m.severity],              // 👈 TWO VALUES
          backgroundColor: ["#008080", "#4db6ac"]
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}




function getWeek() {
  const days = [];
  const now = new Date();
  const utcToday = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));

  for (let i = 6; i >= 0; i--) {
    const d = new Date(utcToday);
    d.setUTCDate(utcToday.getUTCDate() - i);
    days.push(d.toISOString().split("T")[0]);
  }

  return days;
}

let triggerChart = null;

function displayTriggers() {
  if (currTab.value !== "triggers") return;

  const el = document.getElementById("triggerChart");
  if (!el) return;

  if (triggerChart) {
    triggerChart.destroy();
    triggerChart = null;
  }

  const last7 = getWeek();

  const sleepMap = Object.fromEntries(
    weeklyStats.value.sleep.map(s => [s.date, s.hours])
  );

  const stressMap = Object.fromEntries(
    weeklyStats.value.stress.map(s => [s.date, s.rating])
  );

  const mealMap = Object.fromEntries(
    weeklyStats.value.meals.map(m => [m.date, m.count])
  );

  const sleepHours = last7.map(day => sleepMap[day] ?? 0);
  const stressLevels = last7.map(day => stressMap[day] ?? 0);
  const mealCounts = last7.map(day => mealMap[day] ?? 0);

  const labels = last7.map(d =>
    new Date(d).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric"
    })
  );

  const sleepBaseline = last7.map(() => 7);
  const mealBaseline = last7.map(() => 3);

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
          data: mealCounts,
          backgroundColor: "#81d4fa"
        },
        {
          label: "Recommended Sleep",
          data: sleepBaseline,
          type: "line",
          borderColor: "#00695c",
          borderWidth: 2,
          pointRadius: 0,
          borderDash: [6, 6]
        },
        {
          label: "Recommended Daily Meals",
          data: mealBaseline,
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
      plugins: {
        legend: {
          display: true,
          position: "top",
          align: "start"
        }
      },
      scales: {
        y: { beginAtZero: true }
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

async function viewFhirData() {
  try {
    const res = await fetch(`/api/get_patient_info_from_fhir/${userId}`, {
      method: "GET",
      headers: { "accept": "application/json" }
    });

    if (!res.ok) throw new Error("Failed to fetch FHIR data");

    const data = await res.json();

    alert(JSON.stringify(data, null, 2));  // use popup to show for grading/proof of concept
  } catch (err) {
    console.error(err);
    alert("Error fetching FHIR data.");
  }
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
