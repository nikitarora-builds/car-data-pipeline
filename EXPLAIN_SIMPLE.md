# What Does This Project Do? (Simple Explanation)

## Imagine You Have a Toy Box Problem

Imagine you have **35 friends**, and each friend gives you a list of their toy cars.

But here's the problem:
- Your friend **Volkswagen** writes: `"Golf, Red, £28,000, Petrol"`
- Your friend **Audi** writes: `"A4 Saloon, cost: 41900, energy: diesel"`
- Your friend **Toyota** writes: `"Corolla | Hybrid | RRP £27,385"`

Every friend writes the same information in a **completely different way**.

Now imagine your mum says: **"Sort ALL the toy cars into ONE neat list so I can find any car easily."**

That's exactly what this project does — but with **70,785 real cars** from 35 brands.

---

## The 4 Steps (Like Making a Sandwich)

### Step 1: EXTRACT 🗂️ (Pick Up All The Lists)
We go to each friend's house and pick up their list.
- 10 friends give us lists as tables (like a school timetable)
- 1 friend gives us a list in a special computer format (JSON)
- Some lists are messy and hard to read

We collect **all 100,000+ rows** of car information.

### Step 2: TRANSFORM 🔄 (Make Everything The Same)
Now we clean up and rewrite everything in one standard way.

- `"Petrol"`, `"petrol"`, `"PETROL"`, `"Benzin"` → all become → `"PETROL"` ✅
- `"S tronic"`, `"tiptronic"`, `"auto"` → all become → `"AUTOMATIC"` ✅
- Engine size `"1.6"` (in litres) → becomes → `"1600"` (in cc) ✅

Think of it like translating 35 different languages into one language everyone understands.

### Step 3: VALIDATE ✅ (Check For Mistakes)
Before we save anything, we check:
- Is any car missing a price? ❌
- Does any car have a price of £0 or £999,999? Probably wrong ❌
- Is the year 1750? Cars didn't exist then ❌
- Is the same car listed twice? ❌

We give the whole list a **Quality Score** (like a school grade).
If the score drops below 95%, we stop and raise an alarm 🚨

### Step 4: LOAD 💾 (Save The Clean List)
We save the clean, organised list:
- One big file with ALL 70,785 cars
- Separate files per brand (just Audi cars, just BMW cars, etc.)
- Also uploaded to Google's big computer in the sky (BigQuery) ☁️

---

## The Automatic Alarm Clock (Airflow)

Once we built this pipeline, we didn't want to run it by hand every day.

So we set up an **automatic alarm clock** (Apache Airflow) that:
- Wakes up every morning at 6 AM ⏰
- Runs all 4 steps automatically
- Sends an email if something goes wrong 📧
- Tries again 2 more times if it fails 🔁

---

## Why Is This Useful?

Without this pipeline:
- Someone has to manually copy 100,000 rows from 35 different spreadsheets
- It takes days and has lots of human errors
- Every time a brand changes their format, everything breaks

With this pipeline:
- It runs automatically every day
- It catches mistakes before they spread
- Any new brand can be added by writing one small piece of code
- A data analyst can just open the clean file and start working immediately

---

## The Technical Words (For Interviews)

| Simple Word | Technical Word |
|---|---|
| Picking up lists | **Data Ingestion / Extraction** |
| Making everything the same | **Data Normalization / Transformation** |
| Checking for mistakes | **Data Quality Validation** |
| Saving the clean list | **Data Loading** |
| The whole process | **ETL Pipeline** |
| Automatic alarm clock | **Workflow Orchestration (Apache Airflow)** |
| Google's big computer | **GCP BigQuery (Data Warehouse)** |
| Each friend's different format | **Source Schema** |
| Our one standard format | **Target Schema / Unified Schema** |
