RESEARCH ON MIGRAINE TRIGGERS

**Highlighted are most common triggers shared across research**

Resource: Andress-Rothrock, D., King, W., & Rothrock, J. (2009). An Analysis of Migraine Triggers in a Clinic-Based Population. Headache: The Journal of Head and Face Pain, 50(8), 1366–1370. https://doi.org/10.1111/j.1526-4610.2010.01753.x
Most common trigger reported: emotional stress (followed by too much/little sleep, odors, and missing meals)
Those w/ chronic migraines vs episodic migraine similarly report triggers
62% actively cycling females report menses as trigger with 67% of those females reporting their migraine to be more severe compared to their non-menstrual attacks

Resource: Levy, D., Strassman, A. M., & Burstein, R. (2009). A Critical View on the Role of Migraine Triggers in the Genesis of Migraine Pain. Headache: The Journal of Head and Face Pain, 49(6), 953–957. https://doi.org/10.1111/j.1526-4610.2009.01444.x
Most common triggers linked to unbalanced homeostasis (i.e. stress, fatigue, hunger)

Resource: Kelman, L. (2007). The triggers or precipitants of the acute migraine attack. Cephalalgia : An International Journal of Headache, 27(5), 394–402. https://doi.org/10.1111/j.1468-2982.2007.01303.x
Triggers of acute migraine attack (in order of highest → lowest frequency): stress, hormones in women, not eating, weather, sleep disturbance, perfume or odor, neck pain, lights, alcohol, smoke, sleeping late, heat, food, exercise, and sexual activity

Resource: Fukui, P. T., Gonçalves, T. R. T., Strabelli, C. G., Lucchino, N. M. F., Matos, F. C., Santos, J. P. M. dos, Zukerman, E., Zukerman-Guendler, V., Mercante, J. P., Masruha, M. R., Vieira, D. S., & Peres, M. F. P. (2008). Trigger factors in migraine patients. Arquivos de Neuro-Psiquiatria, 66(3a), 494–499. https://doi.org/10.1590/s0004-282x2008000400011
Triggers in general migraine patients (in order of highest → lowest frequency): dietary (fasting), sleep (lack of), environmental, stress, hormonal factors, exertional activities

Resource: Marmura, M. J. (2018). Triggers, Protectors, and Predictors in Episodic Migraine. Current Pain and Headache Reports, 22(12). https://doi.org/10.1007/s11916-018-0734-0
Episodic migraine triggers: stress, menstrual cycle changes, weather changes, sleep disturbances, and alcohol
Premonitory symptoms: neck pain, fatigue, sensitivity to lights, sounds, or odors

Measurements to Capture:
Stress
  -Daily stress level (scale of 1-10 or 1-5)
Sleep/Fatigue
  -Number of hours of sleep OR bedtime/wakeup time
  -Number of hours of sleep simplifies calculation
Odors
  -Daily Y/N exposure to fragrances/odors?
  -Could also exclude this one and focus on stress/sleep/hunger
  -Include free text field or dropdown to capture description of odor (perfume, candle, etc) if we can standardize categories
Missing meals/Hunger
  -Record num of meals that day? Expecting an average of 3 and if below 3 then consider that missing meal - yes (binary?)
  -Or have a user inputted average daily meals and if it falls below that then missing meal = yes
Menses (maybe exclude to avoid differences between those with/without menstrual cycles?)
  -Time migraine occurred (datetime)
  -Migraine intensity (1-5?) 
  -Use GAMS (global assessment of migraine severity)
  -https://www.researchgate.net/publication/332210152_Global_assessment_of_migraine_severity_measure_Preliminary_evidence_of_construct_validity
  -Not at all severe (1), A little severe (2), Somewhat severe (2), Moderately severe (3), Quite severe (4), Very severe (5), Extremely severe (6)
Exercise
  -Daily yes/no
Remedial Medication (NSAIDs, Prescription)
  -Daily yes/no
  
Hypothesis (relationships between triggers) :
Stress/Migraine
  Null: Daily stress level has no impact on migraine occurrence, daily stress level has no impact on migraine severity
Hypothesis: Higher than average stress level increases probability of migraine occurrence/higher migraine intensity
Sleep/Migraine
  Null: Daily sleep level has no impact on migraine occurrence, daily sleep level has no impact on migraine severity
  Hypothesis: Lower than average sleep level increases probability of migraine occurrence/higher migraine intensity
Missing meals/Migraine
  Null: Missing meals has no impact on migraine occurrence, missing meals has no impact on migraine severity
  Hypothesis: Missing meals (yes) increases probability of migraine occurrence/higher migraine intensity
Exposure to odors/migraine
  Null: Exposure to odors (yes) has no impact on migraine occurrence, Exposure to odors (yes)  has no impact on migraine severity
  Hypothesis: Exposure to odors (yes) increases probability of migraine occurrence/higher migraine intensity
Exercise/remedial medication
  Null: Exercise or remedial medication has no impact on migraine occurrence, exercise or remedial medication has no impact on migraine severity
  Hypothesis: Exercise or remedial medication reduces probability of migraine occurrence/higher migraine intensity
  
Relationships to highlight in platform:
Stress level (increased/decreased) - over the past week
Sleep level (increased/decreased) - over the past week
Missing meals (yes/no) count - over the past week 
Perhaps as a percentage, like if 2/7 days had a missed meal
Exposure to odors (yes/no) - over the past week
Similar percentage to missing meals

Set up code/pseudocode for observations (sleep, stress, etc):

Examples (from labs):
 exercise_3_createMedicationRequest(client, medicationName: string): Observable<any> {
   const newMed = {
     //status (should be set to "draft")
     //intent (should be set to "order")
     //subject (should be a reference to the current patient)
     //medicationCodeableConcept.text (should be set to the string passed in by the form)
     resourceType: "MedicationRequest",
     status: "draft",
     intent: "order",
     subject: { reference: `Patient/${client.patient.id}`},
     medicationCodeableConcept: { text: medicationName}
   };
   return from(client.create(newMed));
 }

Sleep
User input: Hours of sleep (daily), datetime = day of input
Example JSONs
{
  "resourceType": "Observation",
  "status": "final",
  "category": [{ "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "survey" }]}],
  "code": {
    "coding": [
      { "system": "http://loinc.org", "code": "93832-4", "display": "Sleep duration" }
    ],
    "text": "Sleep duration (hours)"
  },
  "subject": { "reference": "Patient/{{patientId}}" },
  "effectiveDateTime": "{{datetime}}",
  "valueQuantity": {
    "value": {{hours}},
    "unit": "hours",
    "system": "http://unitsofmeasure.org",
    "code": "h"
  }
}
{


Stress:
User input: daily stress level (1-10)
  "resourceType": "Observation",
  "status": "final",
  "code": {
    "text": "Daily stress level",
    "coding": [{ "system": "http://loinc.org", "code": "72514-3", "display": "Pain severity - rep. (example)" }]
  },
  "subject": { "reference": "Patient/{{patientId}}" },
  "effectiveDateTime": "{{datetime}}",
  "valueInteger": {{stressScore}},
  "note": [{ "text": "Scale 1-10 reported by user." }]
}
Odor exposure:
User input: odor exposure (yes/no) - boolean
User input: text/description (optional)
{
  "resourceType": "Observation",
  "status": "final",
  "code": { "text": "Exposure to odor/fragrance" },
  "subject": { "reference": "Patient/{{patientId}}" },
  "effectiveDateTime": "{{datetime}}",
  "valueBoolean": {{exposed}}, 
  "component": [
    {
      "code": { "text": "Odor description" },
      "valueString": "{{odorDescription}}"   // e.g. "perfume", "candle", or empty
    }
  ]
}


Missed meals:
User input: Number of meals consumed today
{
  "resourceType": "Observation",
  "status": "final",
  "category": [
    {
      "coding": [
        { "system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "survey" }
      ]
    }
  ],
  "code": {
    "coding": [
      { "system": "http://loinc.org", "code": "76457-4", "display": "Number of meals eaten per day" }
    ],
    "text": "Number of meals eaten today"
  },
  "subject": { "reference": "Patient/{{patientId}}" },
  "effectiveDateTime": "{{datetime}}",
  "valueInteger": {{mealsCount}},
  "note": [
    { "text": "User-reported number of meals eaten today. If below personal baseline, considered a missed-meal day." }
  ]
}


Exercise
User input: exercise today (yes/no)
{
  "resourceType": "Observation",
  "status": "final",
  "code": { "text": "Exercise today" },
  "subject": { "reference": "Patient/{{patientId}}" },
  "effectiveDateTime": "{{datetime}}",
  "valueBoolean": {{didExercise}}
}
Remedial medication
User input: taken medication (yes/no)
User input: medication label (text, optional)
{
  "resourceType": "Observation",
  "status": "final",
  "code": { "text": "Rescue medication taken" },
  "subject": { "reference": "Patient/{{patientId}}" },
  "effectiveDateTime": "{{datetime}}",
  "valueBoolean": {{tookMedication}},
  "component": [
    {
      "code": { "text": "Medication name" },
      "valueString": "{{medicationName}}"
    }
  ]
}


Migraine event
User input: migraine (yes/no)
User input: migraine (yes) triggers create migraine observation and intensity question
{
  "resourceType": "Observation",
  "status": "final",
  "category": [{ "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/observation-category","code":"survey"}]}],
  "code": {
    "text": "Migraine event - Global assessment of migraine severity (GAMS)"
  },
  "subject": { "reference": "Patient/{{patientId}}" },
  "effectiveDateTime": "{{migraineDateTime}}",
  "valueInteger": {{gamsScore}},  // e.g. 1..6 per GAMS mapping
  "method": { "text": "Global Assessment of Migraine Severity (GAMS) - single item" },
  "note": [{ "text": "{{freeTextSymptoms}}" }]
}


Push functions:
import { from, Observable } from 'rxjs';
function nowIso(datetime?: string) {
  return datetime ? datetime : new Date().toISOString();
}

function pushObservation(client: any, obs: any): Observable<any> {
  return from(client.create(obs));
}
function createSleepObservation(client: any, hours: number, datetime?: string): Observable<any> {
  const resource = {
    resourceType: "Observation",
    status: "final",
    category: [{ coding: [{ system: "http://terminology.hl7.org/CodeSystem/observation-category", code: "survey" }]}],
    code: {
      coding: [{ system: "http://loinc.org", code: "93832-4", display: "Sleep duration" }],
      text: "Sleep duration (hours)"
    },
    subject: { reference: `Patient/${client.patient.id}`},
    effectiveDateTime: nowIso(datetime),
    valueQuantity: { value: hours, unit: "hours", system: "http://unitsofmeasure.org", code: "h" }
  };
  return from(client.create(resource));
}
function createStressObservation(client: any, stressScore: number, datetime?: string): Observable<any> {
  const resource = {
    resourceType: "Observation",
    status: "final",
    code: { text: "Daily stress level" },
    subject: { reference: `Patient/${client.patient.id}` },
    effectiveDateTime: nowIso(datetime),
    valueInteger: stressScore,
    note: [{ text: "User-reported stress (scale configurable)." }]
  };
  return from(client.create(resource));
}
function createOdorObservation(client: any, exposed: boolean, description?: string, datetime?: string): Observable<any> {
  const resource: any = {
    resourceType: "Observation",
    status: "final",
    code: { text: "Exposure to odor/fragrance" },
    subject: { reference: `Patient/${client.patient.id}` },
    effectiveDateTime: nowIso(datetime),
    valueBoolean: exposed
  };
  if (description) {
    resource.component = [{ code: { text: "Odor description" }, valueString: description }];
  }
  return from(client.create(resource));
}
function createMissedMealObservation(client: any, missedMeal: boolean, mealsCount?: number, datetime?: string): Observable<any> {
  const resource: any = {
    resourceType: "Observation",
    status: "final",
    code: { text: "Missed meals today" },
    subject: { reference: `Patient/${client.patient.id}` },
    effectiveDateTime: nowIso(datetime),
    valueBoolean: missedMeal
  };
  if (typeof mealsCount === 'number') {
    resource.component = [{ code: { text: "Meals count today" }, valueInteger: mealsCount }];
  }
  return from(client.create(resource));
}
function createExerciseObservation(client: any, exercised: boolean, datetime?: string): Observable<any> {
  const resource = {
    resourceType: "Observation",
    status: "final",
    code: { text: "Exercise today" },
    subject: { reference: `Patient/${client.patient.id}` },
    effectiveDateTime: nowIso(datetime),
    valueBoolean: exercised
  };
  return from(client.create(resource));
}

function createMedicationTakenObservation(client: any, tookMedication: boolean, medName?: string, datetime?: string): Observable<any> {
  const resource: any = {
    resourceType: "Observation",
    status: "final",
    code: { text: "Rescue medication taken" },
    subject: { reference: `Patient/${client.patient.id}` },
    effectiveDateTime: nowIso(datetime),
    valueBoolean: tookMedication
  };
  if (medName) {
    resource.component = [{ code: { text: "Medication name" }, valueString: medName }];
  }
  return from(client.create(resource));
}

/** Migraine event with GAMS score (1..6) */
function createMigraineObservation(client: any, gamsScore: number, migraineDateTime?: string, notes?: string): Observable<any> {
  const resource: any = {
    resourceType: "Observation",
    status: "final",
    category: [{ coding: [{ system: "http://terminology.hl7.org/CodeSystem/observation-category", code: "survey" }]}],
    code: { text: "Migraine event - GAMS" },
    subject: { reference: `Patient/${client.patient.id}`},
    effectiveDateTime: nowIso(migraineDateTime),
    valueInteger: gamsScore,
    method: { text: "Global Assessment of Migraine Severity (GAMS)" }
  };
  if (notes) resource.note = [{ text: notes }];
  return from(client.create(resource));
}

function pushDailyObservationsBundle(client: any, patientId: string, observations: any[]): Observable<any> {
  const entries = observations.map(obs => ({
    request: { method: "POST", url: "Observation" },
    resource: { ...obs, subject: { reference: `Patient/${patientId}` } }
  }));
  const bundle = {
    resourceType: "Bundle",
    type: "transaction",
    entry: entries
  };
  return from(client.transaction(bundle)); // or client.create(bundle) depending on your client
}

const obsList = [
  // resources like those above (NOT including subject)
];
pushDailyObservationsBundle(client, client.patient.id, obsList).subscribe(...);
*/

Set up code/pseudocode for migraine prediction:

stress = userInput.stress 
sleep = userInput.sleepHours
meals = userInput.mealsCount   
odor = userInput.odorExposure    - bool
exercise = userInput.exercise    - bool
datetime = currentDateTime

missedMeal = (meals < 3) ? 1 : 0
lowSleep = (sleep < 6) ? 1 : 0
highStress = (stress > 5) ? 1 : 0
odorExposure = odor ? 1 : 0
// Assign weights (more research needed to determine weight)
weightStress = 0.x
weightSleep = 0.x
weightMeals = 0.x
weightOdor = 0.x

// Compute risk score (0 to 1 scale)
riskScore = (
   (highStress * weightStress) +
   (lowSleep * weightSleep) +
   (missedMeal * weightMeals) +
   (odorExposure * weightOdor)
)

// Normalize to 0–100%
riskPercent = riskScore * 100

// Determine qualitative risk level
if (riskPercent < 25):
    riskLevel = "Low"
else if (riskPercent < 60):
    riskLevel = "Moderate"
else:
    riskLevel = "High"

// Output prediction result
return {
   "riskLevel": riskLevel,
   "riskPercent": riskPercent,
   "date": datetime,
   "explanation": [
      if highStress then "High stress today" else "",
      if lowSleep then "Low sleep hours" else "",
      if missedMeal then "Missed meal(s)" else "",
      if odorExposure then "Odor exposure" else ""
   ].filter(not empty)
}

Set up personal health recommendation language/pseudocode: 
May need to determine weights to determine language and primary factor leading to migraine
Add prediction factor to UI predicting likelihood of a migraine based off of risk/probability score from past 24 hours?
