import pandas as pd


class AllocationEngine:
    """Encapsulates merit-based subject allocation behavior."""

    def __init__(self, preference_columns=None, unallocated_label="UNALLOCATED"):
        self.preference_columns = preference_columns or ["Pref_1", "Pref_2", "Pref_3"]
        self.unallocated_label = unallocated_label

    def _build_subject_capacities(self, subjects_df):
        return subjects_df.set_index("Subject_ID")["Capacity"].to_dict()

    def _extract_preferences(self, student_row):
        return [student_row.get(pref_col) for pref_col in self.preference_columns]

    def allocate(self, students_df, subjects_df):
        subject_capacities = self._build_subject_capacities(subjects_df)
        allocations = {subj: [] for subj in subject_capacities}
        student_assignments = []

        ranked_students = students_df.sort_values(by="Marks", ascending=False)

        for _, student in ranked_students.iterrows():
            assigned_subject = self._assign_student(student, subject_capacities, allocations)
            student_assignments.append(self._build_assignment_row(student, assigned_subject))

        return pd.DataFrame(student_assignments)

    def _assign_student(self, student, subject_capacities, allocations):
        preferences = self._extract_preferences(student)
        student_id = student["Student_ID"]

        for preferred_subject in preferences:
            if pd.notna(preferred_subject) and preferred_subject in subject_capacities:
                if len(allocations[preferred_subject]) < subject_capacities[preferred_subject]:
                    allocations[preferred_subject].append(student_id)
                    return preferred_subject

        return self.unallocated_label

    def _build_assignment_row(self, student, assigned_subject):
        return {
            "Student_ID": student["Student_ID"],
            "Name": student["Name"],
            "Department": student["Department"],
            "Marks": student["Marks"],
            "Assigned_Subject": assigned_subject,
        }


# Backward-compatible functional wrapper
_allocation_engine = AllocationEngine()


def allocate(students_df, subjects_df):
    return _allocation_engine.allocate(students_df, subjects_df)