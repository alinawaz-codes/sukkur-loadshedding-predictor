# ⚡ Sukkur Load Shedding Predictor

An interactive dashboard that shows the load shedding timing of 32 areas of Sukkur city and uses a small Machine Learning model to estimate the **chance of load shedding** on any selected date.

**Live app link:** https://sukkur-loadshedding-app.streamlit.app/

> **Note:** The area timings and the training history in this project are **sample data** created for a university project. They are **not** official SEPCO schedules.

## Features

- Select an area and a date, then click **Predict**. No data typing is needed.
- Shows the expected light **off time**, **on time**, and total off duration.
- Live status box (ON / OFF) with a **countdown** that updates every second (Pakistan time).
- **Pie chart** of ON vs OFF hours for the day.
- **24-hour timeline** (12 AM to 12 AM) with the outage window highlighted.
- **7-day chart** showing the chance of load shedding for the next week.
- **Tomorrow's prediction** with the expected timing.
- Works on desktop and on phone.

## How it works

1. Every area has **one fixed daily timing** (light off time and light on time), stored in `data/area_timings.csv`.
2. A **Random Forest Classifier** learns from one year of sample history (`data/history.csv`) and predicts how likely load shedding is on a given day.
3. Model inputs: **area**, **weekday**, and **temperature**. Temperature is not typed by the user; the app uses the average temperature of the selected month in Sukkur.
4. Model output: **chance of load shedding (%)**. If the chance is below 50%, the app says load shedding is unlikely on that date.
5. All times use **Pakistan time** (Asia/Karachi).

## Tech stack

- Python
- Streamlit (dashboard)
- Pandas and NumPy (data)
- Scikit-learn (Random Forest)
- Plotly (charts)

## Project structure

```
sukkur-loadshedding-predictor/
├── app.py               # Streamlit dashboard (run this file)
├── model.py             # Random Forest model
├── logic.py             # Helper functions: time, countdown, temperature
├── generate_data.py     # Creates the two sample CSV files
├── requirements.txt     # Python packages
├── data/
│   ├── area_timings.csv # One sample timing for each of the 32 areas
│   └── history.csv      # One year of sample history for training
└── .streamlit/
    └── config.toml      # Theme settings
```

## Run locally

```
pip install -r requirements.txt
python -m streamlit run app.py
```

Then open http://localhost:8501 in your browser.

To change a timing, edit `data/area_timings.csv` (use 24-hour time, for example `14:30`) and restart the app.

## Limitations

- Timings and history are **sample data**, so the model accuracy shown in the app (about 89%) is measured on sample data only and is not real-world accuracy.
- Real load shedding follows electricity feeders, not road names. This is an **area-based estimate**, not an official feeder schedule.
- The ON/OFF status is the **expected status** from the predicted schedule. The app has no live sensor or official data feed.
- Only three inputs are used (area, weekday, temperature). Real outages also depend on demand, faults, and maintenance.

## Future work

- Train on real outage records collected from residents or the utility.
- Add feeder-wise schedules and multiple outages per day.
- Add live weather data and fault or maintenance notices.
- Add Urdu language support and mobile notifications.

## Author

**Ali Nawaz**
BS Artificial Intelligence Engineering
Dawood University of Engineering & Technology (DUET), Karachi
Subject: PYTHON FOR AI
