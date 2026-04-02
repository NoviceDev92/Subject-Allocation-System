import pandas as pd

def allocate(students_df, subjects_df):
    subject_capacities = subjects_df.set_index('Subject_ID')['Capacity'].to_dict()
    allocations = {subj: [] for subj in subject_capacities.keys()}
    student_assignments = []

    students_df = students_df.sort_values(by='Marks', ascending=False)

    for _, student in students_df.iterrows():
        assigned = False
        student_id = student['Student_ID']
        preferences = [student.get('Pref_1'), student.get('Pref_2'), student.get('Pref_3')]
        
        for pref in preferences:
            if pd.notna(pref) and pref in subject_capacities:
                if len(allocations[pref]) < subject_capacities[pref]:
                    allocations[pref].append(student_id)
                    student_assignments.append({
                        'Student_ID': student_id,
                        'Name': student['Name'],
                        'Department': student['Department'],
                        'Marks': student['Marks'],
                        'Assigned_Subject': pref
                    })
                    assigned = True
                    break
        
        if not assigned:
            student_assignments.append({
                'Student_ID': student_id,
                'Name': student['Name'],
                'Department': student['Department'],
                'Marks': student['Marks'],
                'Assigned_Subject': 'UNALLOCATED'
            })

    return pd.DataFrame(student_assignments)