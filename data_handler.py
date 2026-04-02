import pandas as pd

def load_data(file):
    return pd.read_csv(file)

def get_student_info(df, student_id):
    return df[df['Student_ID'].astype(str) == str(student_id)]

def get_subject_students(df, subject_id):
    return df[df['Assigned_Subject'] == subject_id]

def get_department_mapping(df):
    return df.groupby(['Department', 'Assigned_Subject']).size().reset_index(name='Count')

def export_data(df):
    return df.to_csv(index=False).encode('utf-8')