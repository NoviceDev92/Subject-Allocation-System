import pandas as pd


class DataHandler:
    """Service class for data loading, querying, and export."""

    def load_data(self, file):
        return pd.read_csv(file)

    def get_student_info(self, df, student_id):
        return df[df["Student_ID"].astype(str) == str(student_id)]

    def get_subject_students(self, df, subject_id):
        return df[df["Assigned_Subject"] == subject_id]

    def get_department_mapping(self, df):
        return df.groupby(["Department", "Assigned_Subject"]).size().reset_index(name="Count")

    def export_data(self, df):
        return df.to_csv(index=False).encode("utf-8")


# Backward-compatible functional wrappers
_data_handler = DataHandler()


def load_data(file):
    return _data_handler.load_data(file)


def get_student_info(df, student_id):
    return _data_handler.get_student_info(df, student_id)


def get_subject_students(df, subject_id):
    return _data_handler.get_subject_students(df, subject_id)


def get_department_mapping(df):
    return _data_handler.get_department_mapping(df)


def export_data(df):
    return _data_handler.export_data(df)