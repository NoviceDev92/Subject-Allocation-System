import pandas as pd
from io import BytesIO


class DataHandler:
    """Service class for data loading, querying, and export."""

    def load_data(self, file):
        file_name = getattr(file, "name", "").lower()
        if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            return pd.read_excel(file)
        return pd.read_csv(file)

    def get_student_info(self, df, student_id):
        return df[df["Student_ID"].astype(str) == str(student_id)]

    def get_subject_students(self, df, subject_id):
        return df[df["Assigned_Subject"] == subject_id]

    def get_department_mapping(self, df):
        return df.groupby(["Department", "Assigned_Subject"]).size().reset_index(name="Count")

    def mask_names(self, df):
        masked = df.copy()
        if "Name" not in masked.columns:
            return masked
        masked["Name"] = masked["Student_ID"].astype(str).apply(lambda sid: f"Student_{sid}")
        return masked

    def apply_reveal_policy(self, df, reveal=False):
        if reveal:
            return df
        return self.mask_names(df)

    def export_data(self, df):
        return df.to_csv(index=False).encode("utf-8")

    def export_excel_by_department(self, df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Master")
            for department in sorted(df["Department"].dropna().astype(str).unique()):
                department_df = df[df["Department"].astype(str) == department]
                safe_name = department[:31] if department else "Unknown"
                department_df.to_excel(writer, index=False, sheet_name=safe_name)
        output.seek(0)
        return output.getvalue()


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