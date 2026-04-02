import plotly.express as px
import pandas as pd

def plot_allocation_status(df):
    status_counts = df['Assigned_Subject'].apply(lambda x: 'Unallocated' if x == 'UNALLOCATED' else 'Allocated').value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig = px.pie(status_counts, values='Count', names='Status', title='Overall Allocation Status', hole=0.4)
    return fig

def plot_subject_popularity(df):
    allocated_only = df[df['Assigned_Subject'] != 'UNALLOCATED']
    subj_counts = allocated_only['Assigned_Subject'].value_counts().reset_index()
    subj_counts.columns = ['Subject', 'Students Enrolled']
    fig = px.bar(subj_counts, x='Subject', y='Students Enrolled', title='Students per Subject', color='Subject')
    return fig

def plot_department_distribution(df):
    allocated_only = df[df['Assigned_Subject'] != 'UNALLOCATED']
    dept_subj_counts = allocated_only.groupby(['Department', 'Assigned_Subject']).size().reset_index(name='Count')
    fig = px.bar(dept_subj_counts, x='Department', y='Count', color='Assigned_Subject', title='Subject Distribution across Departments', barmode='stack')
    return fig