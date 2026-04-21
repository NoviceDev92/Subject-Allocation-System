# Subject Allocation System

BCSE-II 4th Semester Advanced OOPS Group Project

## Overview

This project is a merit-based elective subject allocation web app built with Streamlit.
It allocates students to subjects using marks and ordered preferences while respecting
seat capacities. It also supports tie intervention, waitlisting, anonymized display,
analytics, and downloadable outputs.

## Core Features

- Merit-first allocation with dynamic preference columns (`Pref_1 ... Pref_n`)
- Tie detection with pause-and-resume manual review
- Temporary `WAITLISTED` status for tied candidates during intervention
- Manual post-allocation reassignment with capacity checks
- Anonymous names by default with explicit reveal action
- Exports:
  - CSV output
  - Excel output with `Master` + department-wise sheets
- Analytics dashboard using Plotly
- Dockerized deployment (`Dockerfile` + `docker-compose.yml`)

## Project Structure

- `app.py` - Streamlit UI and workflow orchestration
- `allocator.py` - Allocation engine (OOP), tie logic, seat-state methods
- `data_handler.py` - File loading, masking, filters, export helpers
- `visualizer.py` - Plotly chart builders
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container image build instructions
- `docker-compose.yml` - Container runtime service definition

## Input Files

### Students Input

Supported formats:
- `.csv`
- `.xlsx`
- `.xls`

The app supports:
- canonical CSV style (`Student_ID`, `Name`, `Department`, `Marks`, `Pref_*`)
- Google Form style Excel sheets with preference columns like
  `Preference Selection of Open Elective Courses [Preference n]`

### Subjects Input

Use CSV/Excel with columns:
- `Subject_ID`
- `Subject_Name`
- `Capacity`

Sample files included:
- `students.csv`
- `subjects.csv`
- `students_tie_demo.csv`
- `subjects_tie_demo.csv`
- `subjects_from_option_form.csv`

## Run Locally (Python)

```powershell
cd "C:\Users\SOMDEV\OneDrive\ドキュメント\Subject-Allocation-System"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open: `http://localhost:8501`

## Run with Docker Compose

```powershell
cd "C:\Users\SOMDEV\OneDrive\ドキュメント\Subject-Allocation-System"
docker compose up --build
```

Open: `http://localhost:8501`

To stop:

```powershell
docker compose down
```

## Run from Docker Hub Image

```powershell
docker pull nihsom/subject-allocation-system:latest
docker run -p 8501:8501 nihsom/subject-allocation-system:latest
```

Open: `http://localhost:8501`

## How Tie Intervention Works

1. Allocation runs by marks in descending order.
2. If a same-marks group exceeds remaining seats for a subject boundary:
   - allocation pauses
   - contenders are shown as `WAITLISTED`
   - admin manually selects winners
3. Allocation resumes until next tie or completion.

## Privacy Behavior

- Names are hidden by default.
- Names are revealed only after explicit prompt action in the sidebar.

## Team

- Somdev Ganguli (002410501033)
- Vibhan Dutta (002410501041)
- Romit Datta (002410501032)
- Suprit Banerjee (002410501052)
- Golam Masum Basar (002410501057)
