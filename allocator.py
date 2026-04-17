import re
import pandas as pd


class AllocationEngine:
    """Encapsulates merit-based subject allocation behavior with tie intervention."""

    def __init__(self, preference_columns=None, unallocated_label="UNALLOCATED"):
        self.preference_columns = preference_columns
        self.unallocated_label = unallocated_label

    def _build_subject_capacities(self, subjects_df):
        return subjects_df.set_index("Subject_ID")["Capacity"].to_dict()

    def _discover_preference_columns(self, students_df):
        if self.preference_columns:
            return [col for col in self.preference_columns if col in students_df.columns]

        pref_cols = [col for col in students_df.columns if str(col).startswith("Pref_")]

        def _pref_key(col_name):
            match = re.search(r"(\d+)$", str(col_name))
            return int(match.group(1)) if match else 10**9

        return sorted(pref_cols, key=_pref_key)

    def _extract_department(self, raw_value):
        if pd.isna(raw_value):
            return "UNKNOWN"
        text = str(raw_value).strip()
        if "-" in text:
            return text.split("-", 1)[0].strip().upper()
        return text.upper()

    def _extract_marks_series(self, students_df):
        if "Marks" in students_df.columns:
            return pd.to_numeric(students_df["Marks"], errors="coerce")

        sgpa_cols = [col for col in students_df.columns if "obtained sgpa" in str(col).lower()]
        if not sgpa_cols:
            return pd.Series([None] * len(students_df), index=students_df.index)

        marks = pd.to_numeric(students_df[sgpa_cols[0]], errors="coerce")
        for col in sgpa_cols[1:]:
            marks = marks.fillna(pd.to_numeric(students_df[col], errors="coerce"))
        return marks

    def _extract_preference_columns_from_form(self, students_df):
        pref_cols = [col for col in students_df.columns if "preference" in str(col).lower()]
        grouped = {}
        for col in pref_cols:
            match = re.search(r"\[Preference\s*(\d+)\]", str(col), flags=re.IGNORECASE)
            if not match:
                continue
            pref_num = int(match.group(1))
            grouped.setdefault(pref_num, []).append(col)

        normalized_prefs = {}
        for pref_num, cols in grouped.items():
            series = students_df[cols[0]]
            for col in cols[1:]:
                series = series.fillna(students_df[col])
            normalized_prefs[f"Pref_{pref_num}"] = series
        return normalized_prefs

    def _map_preference_value_to_subject_id(self, preference_value, subjects_df):
        if pd.isna(preference_value):
            return preference_value

        raw = str(preference_value).strip()
        if not raw:
            return raw

        subject_ids = {str(x).strip(): str(x).strip() for x in subjects_df.get("Subject_ID", pd.Series([], dtype=str))}
        if raw in subject_ids:
            return raw

        name_map = {}
        if "Subject_Name" in subjects_df.columns:
            for _, row in subjects_df.iterrows():
                subject_id = str(row["Subject_ID"]).strip()
                subject_name = str(row["Subject_Name"]).strip().lower()
                name_map[subject_name] = subject_id
                short_match = re.search(r"\(([^)]+)\)", str(row["Subject_Name"]))
                if short_match:
                    name_map[short_match.group(1).strip().lower()] = subject_id

        lower_raw = raw.lower()
        if lower_raw in name_map:
            return name_map[lower_raw]

        bracket_match = re.search(r"\(([^)]+)\)", raw)
        if bracket_match:
            key = bracket_match.group(1).strip().lower()
            if key in name_map:
                return name_map[key]

        if "Subject_Name" in subjects_df.columns:
            cleaned_raw = re.sub(r"[^a-z0-9 ]", " ", lower_raw)
            cleaned_raw = re.sub(r"\s+", " ", cleaned_raw).strip()
            for _, row in subjects_df.iterrows():
                candidate_name = str(row["Subject_Name"]).lower().strip()
                cleaned_candidate = re.sub(r"[^a-z0-9 ]", " ", candidate_name)
                cleaned_candidate = re.sub(r"\s+", " ", cleaned_candidate).strip()
                if cleaned_candidate and (cleaned_candidate in cleaned_raw or cleaned_raw in cleaned_candidate):
                    return str(row["Subject_ID"]).strip()

        return raw

    def _normalize_students_df(self, students_df, subjects_df):
        required = {"Student_ID", "Name", "Department", "Marks"}
        if required.issubset(set(students_df.columns)):
            normalized = students_df.copy()
        else:
            student_id_col = None
            for candidate in ["Full 12-digit Class Roll Number", "Class Roll Number", "Roll Number", "Student_ID"]:
                if candidate in students_df.columns:
                    student_id_col = candidate
                    break

            name_col = None
            for candidate in ["Full Name (as In Roll Sheet)", "Full Name", "Name"]:
                if candidate in students_df.columns:
                    name_col = candidate
                    break

            dept_col = None
            for candidate in ["Department and Year of Study in the session 2023-2024", "Department", "Branch"]:
                if candidate in students_df.columns:
                    dept_col = candidate
                    break

            normalized = pd.DataFrame(
                {
                    "Student_ID": students_df[student_id_col].astype(str) if student_id_col else students_df.index.astype(str),
                    "Name": students_df[name_col] if name_col else "UNKNOWN",
                    "Department": students_df[dept_col].apply(self._extract_department) if dept_col else "UNKNOWN",
                    "Marks": self._extract_marks_series(students_df),
                }
            )

            form_preferences = self._extract_preference_columns_from_form(students_df)
            for col_name, values in form_preferences.items():
                normalized[col_name] = values

        preference_columns = self._discover_preference_columns(normalized)
        for pref_col in preference_columns:
            normalized[pref_col] = normalized[pref_col].apply(
                lambda x: self._map_preference_value_to_subject_id(x, subjects_df)
            )

        normalized["Marks"] = pd.to_numeric(normalized["Marks"], errors="coerce").fillna(-1)
        return normalized

    def initialize_state(self, students_df, subjects_df):
        normalized_students_df = self._normalize_students_df(students_df, subjects_df)
        preference_columns = self._discover_preference_columns(normalized_students_df)
        ranked_students = normalized_students_df.sort_values(by="Marks", ascending=False, kind="mergesort").reset_index(drop=True)
        subject_capacities = self._build_subject_capacities(subjects_df)
        return {
            "ranked_students": ranked_students,
            "subject_capacities": subject_capacities,
            "allocations": {subj: [] for subj in subject_capacities},
            "student_assignments": [],
            "cursor": 0,
            "preference_columns": preference_columns,
            "pending_tie": None,
            "waitlisted_students": [],
            "status": "running",
        }

    def run_until_pause_or_complete(self, state):
        if state["pending_tie"] is not None:
            state["status"] = "paused"
            return state

        while state["cursor"] < len(state["ranked_students"]):
            self.run_next_group(state)
            if state["status"] == "paused":
                return state

        state["status"] = "completed"
        return state

    def run_next_group(self, state):
        if state["pending_tie"] is not None:
            state["status"] = "paused"
            return state

        students = state["ranked_students"]
        if state["cursor"] >= len(students):
            state["status"] = "completed"
            return state

        current_mark = students.iloc[state["cursor"]]["Marks"]
        next_idx = state["cursor"]
        group_rows = []
        while next_idx < len(students) and students.iloc[next_idx]["Marks"] == current_mark:
            group_rows.append(students.iloc[next_idx].to_dict())
            next_idx += 1

        tie_payload = self._detect_tie_in_group(state, group_rows)
        if tie_payload:
            tie_payload["next_index"] = next_idx
            tie_payload["group_rows"] = group_rows
            state["pending_tie"] = tie_payload
            state["waitlisted_students"] = [
                self._build_assignment_row(row, "WAITLISTED") for row in tie_payload["candidates"]
            ]
            state["status"] = "paused"
            return state

        self._assign_group_without_pause(state, group_rows)
        state["cursor"] = next_idx
        state["status"] = "running" if state["cursor"] < len(students) else "completed"
        return state

    def apply_tie_resolution(self, state, selected_student_ids):
        pending = state.get("pending_tie")
        if not pending:
            raise ValueError("No pending tie found.")

        selected_student_ids = {str(student_id) for student_id in selected_student_ids}
        candidate_rows = pending["candidates"]
        seat_count = pending["seat_count"]
        subject_id = pending["subject_id"]

        valid_candidate_ids = {str(row["Student_ID"]) for row in candidate_rows}
        if not selected_student_ids.issubset(valid_candidate_ids):
            raise ValueError("Selected IDs must be from the tied candidate list.")
        if len(selected_student_ids) != seat_count:
            raise ValueError(f"You must select exactly {seat_count} student(s).")

        winners = []
        remaining_group = []
        for row in pending["group_rows"]:
            if str(row["Student_ID"]) in selected_student_ids and str(row["Student_ID"]) in valid_candidate_ids:
                winners.append(row)
            else:
                remaining_group.append(row)

        for winner in winners:
            state["allocations"][subject_id].append(winner["Student_ID"])
            state["student_assignments"].append(self._build_assignment_row(winner, subject_id))

        state["pending_tie"] = None
        state["waitlisted_students"] = []
        followup_tie = self._detect_tie_in_group(state, remaining_group)
        if followup_tie:
            followup_tie["next_index"] = pending["next_index"]
            followup_tie["group_rows"] = remaining_group
            state["pending_tie"] = followup_tie
            state["waitlisted_students"] = [
                self._build_assignment_row(row, "WAITLISTED") for row in followup_tie["candidates"]
            ]
            state["status"] = "paused"
            return state

        self._assign_group_without_pause(state, remaining_group)
        state["cursor"] = pending["next_index"]
        state["status"] = "running"
        return self.run_until_pause_or_complete(state)

    def allocate(self, students_df, subjects_df):
        state = self.initialize_state(students_df, subjects_df)
        state = self.run_until_pause_or_complete(state)
        while state["status"] == "paused":
            pending = state["pending_tie"]
            auto_winners = [str(row["Student_ID"]) for row in pending["candidates"][: pending["seat_count"]]]
            state = self.apply_tie_resolution(state, auto_winners)
        return self.state_to_dataframe(state)

    def state_to_dataframe(self, state):
        return pd.DataFrame(state["student_assignments"])

    def get_seat_status(self, state):
        capacities = state["subject_capacities"]
        rows = []
        for subject_id, cap in capacities.items():
            occupied = len(state["allocations"][subject_id])
            rows.append(
                {
                    "Subject_ID": subject_id,
                    "Occupied_Seats": occupied,
                    "Capacity": cap,
                    "Remaining_Seats": max(cap - occupied, 0),
                }
            )
        return pd.DataFrame(rows).sort_values("Subject_ID")

    def _extract_preferences(self, student_row, preference_columns):
        return [student_row.get(pref_col) for pref_col in preference_columns]

    def _find_best_available_subject(self, student_row, preference_columns, subject_capacities, allocations):
        for preferred_subject in self._extract_preferences(student_row, preference_columns):
            if pd.notna(preferred_subject) and preferred_subject in subject_capacities:
                if len(allocations[preferred_subject]) < subject_capacities[preferred_subject]:
                    return preferred_subject
        return None

    def _assign_group_without_pause(self, state, group_rows):
        for row in group_rows:
            assigned = self._find_best_available_subject(
                row,
                state["preference_columns"],
                state["subject_capacities"],
                state["allocations"],
            )
            if assigned is not None:
                state["allocations"][assigned].append(row["Student_ID"])
                state["student_assignments"].append(self._build_assignment_row(row, assigned))
            else:
                state["student_assignments"].append(self._build_assignment_row(row, self.unallocated_label))

    def _detect_tie_in_group(self, state, group_rows):
        candidate_map = {}
        for row in group_rows:
            best_subject = self._find_best_available_subject(
                row,
                state["preference_columns"],
                state["subject_capacities"],
                state["allocations"],
            )
            if best_subject is not None:
                candidate_map.setdefault(best_subject, []).append(row)

        for subject_id, candidates in candidate_map.items():
            remaining = state["subject_capacities"][subject_id] - len(state["allocations"][subject_id])
            if remaining > 0 and len(candidates) > remaining:
                return {
                    "subject_id": subject_id,
                    "seat_count": remaining,
                    "candidates": candidates,
                    "marks": candidates[0]["Marks"] if candidates else None,
                }
        return None

    def _build_assignment_row(self, student, assigned_subject):
        return {
            "Student_ID": student["Student_ID"],
            "Name": student["Name"],
            "Department": student["Department"],
            "Marks": student["Marks"],
            "Assigned_Subject": assigned_subject,
        }


_allocation_engine = AllocationEngine()


def allocate(students_df, subjects_df):
    return _allocation_engine.allocate(students_df, subjects_df)