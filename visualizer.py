import plotly.express as px
import pandas as pd


class AllocationVisualizer:
    """Builds Plotly figures for allocation insights."""

    def __init__(self, unallocated_label="UNALLOCATED"):
        self.unallocated_label = unallocated_label

    def plot_allocation_status(self, df):
        status_counts = (
            df["Assigned_Subject"]
            .apply(lambda x: "Unallocated" if x == self.unallocated_label else "Allocated")
            .value_counts()
            .reset_index()
        )
        status_counts.columns = ["Status", "Count"]
        return px.pie(
            status_counts,
            values="Count",
            names="Status",
            title="Overall Allocation Status",
            hole=0.4,
        )

    def plot_subject_popularity(self, df):
        allocated_only = df[df["Assigned_Subject"] != self.unallocated_label]
        subj_counts = allocated_only["Assigned_Subject"].value_counts().reset_index()
        subj_counts.columns = ["Subject", "Students Enrolled"]
        return px.bar(
            subj_counts,
            x="Subject",
            y="Students Enrolled",
            title="Students per Subject",
            color="Subject",
        )

    def plot_department_distribution(self, df):
        allocated_only = df[df["Assigned_Subject"] != self.unallocated_label]
        dept_subj_counts = (
            allocated_only.groupby(["Department", "Assigned_Subject"]).size().reset_index(name="Count")
        )
        return px.bar(
            dept_subj_counts,
            x="Department",
            y="Count",
            color="Assigned_Subject",
            title="Subject Distribution across Departments",
            barmode="stack",
        )


# Backward-compatible functional wrappers
_allocation_visualizer = AllocationVisualizer()


def plot_allocation_status(df):
    return _allocation_visualizer.plot_allocation_status(df)


def plot_subject_popularity(df):
    return _allocation_visualizer.plot_subject_popularity(df)


def plot_department_distribution(df):
    return _allocation_visualizer.plot_department_distribution(df)