import streamlit as st
import pandas as pd
import time
from data_handler import DataHandler
from allocator import AllocationEngine
from visualizer import AllocationVisualizer

st.set_page_config(page_title="Course Allocation System", layout="wide")

st.title("Merit-Based Course Allocation System")

data_handler = DataHandler()
allocation_engine = AllocationEngine()
visualizer = AllocationVisualizer()

with st.sidebar:
    st.header("Data Input")
    students_file = st.file_uploader("Upload Students File", type=["csv", "xlsx", "xls"])
    subjects_file = st.file_uploader("Upload Subjects File", type=["csv", "xlsx", "xls"])
    st.divider()
    st.subheader("Identity Privacy")
    if "reveal_names" not in st.session_state:
        st.session_state.reveal_names = False
    reveal_phrase = st.text_input("Type REVEAL to show names", type="password")
    if st.button("Apply Name Visibility"):
        st.session_state.reveal_names = reveal_phrase == "REVEAL"
        if st.session_state.reveal_names:
            st.success("Names revealed for this session.")
        else:
            st.info("Names remain anonymized.")


def _get_display_df(df):
    return data_handler.apply_reveal_policy(df, reveal=st.session_state.get("reveal_names", False))


def _render_seat_status(state):
    st.subheader("Seat Occupancy")
    st.caption("Legend: 🟩 Occupied | 🟥 Contested tie seats | ⬜ Available")
    seat_df = allocation_engine.get_seat_status(state)
    pending_tie = state.get("pending_tie")
    contested_subject = pending_tie["subject_id"] if pending_tie else None
    contested_remaining = pending_tie["seat_count"] if pending_tie else 0

    def _seat_string(capacity, occupied, is_contested=False, contested_seats=0):
        seat_chars = []
        for idx in range(capacity):
            if idx < occupied:
                seat_chars.append("🟩")
            elif is_contested and (idx - occupied) < contested_seats:
                seat_chars.append("🟥")
            else:
                seat_chars.append("⬜")
        rows = ["".join(seat_chars[i : i + 10]) for i in range(0, len(seat_chars), 10)]
        return "\n".join(rows)

    for row in seat_df.itertuples(index=False):
        occupied = int(row.Occupied_Seats)
        cap = int(row.Capacity)
        ratio = (occupied / cap) if cap else 0
        st.write(f"**{row.Subject_ID}**: {occupied}/{cap} seats occupied")
        st.progress(ratio)
        seat_map = _seat_string(
            cap,
            occupied,
            is_contested=(row.Subject_ID == contested_subject),
            contested_seats=int(contested_remaining),
        )
        st.markdown(f"```text\n{seat_map}\n```")
    st.dataframe(seat_df, use_container_width=True)


def _apply_manual_override(allocated_df, student_id, new_subject, subjects_df, force_override):
    updated = allocated_df.copy()
    student_mask = updated["Student_ID"].astype(str) == str(student_id)
    if not student_mask.any():
        return allocated_df, "Student not found.", True

    if new_subject != allocation_engine.unallocated_label:
        capacities = subjects_df.set_index("Subject_ID")["Capacity"].to_dict()
        if new_subject not in capacities:
            return allocated_df, "Selected subject does not exist.", True
        current_count = (updated["Assigned_Subject"] == new_subject).sum()
        old_subject = updated.loc[student_mask, "Assigned_Subject"].iloc[0]
        if old_subject == new_subject:
            return allocated_df, "Student is already assigned to this subject.", True
        if current_count >= capacities[new_subject] and not force_override:
            return allocated_df, "Target subject is full. Enable force override to continue.", True

    updated.loc[student_mask, "Assigned_Subject"] = new_subject
    return updated, "Manual override applied successfully.", False

if students_file and subjects_file:
    students_df = data_handler.load_data(students_file)
    subjects_df = data_handler.load_data(subjects_file)

    if "allocated_df" not in st.session_state:
        st.session_state.allocated_df = None
    if "allocation_state" not in st.session_state:
        st.session_state.allocation_state = None
    if "edit_log" not in st.session_state:
        st.session_state.edit_log = []

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Start / Continue Allocation", use_container_width=True):
            if st.session_state.allocation_state is None:
                st.session_state.allocation_state = allocation_engine.initialize_state(students_df, subjects_df)
            st.session_state.allocation_state = allocation_engine.run_until_pause_or_complete(
                st.session_state.allocation_state
            )
            if st.session_state.allocation_state["status"] == "completed":
                st.session_state.allocated_df = allocation_engine.state_to_dataframe(st.session_state.allocation_state)
                st.success("Allocation completed successfully.")
            else:
                st.warning("Allocation paused for tie intervention.")
    with col_b:
        if st.button("Reset Allocation Run", use_container_width=True):
            st.session_state.allocation_state = None
            st.session_state.allocated_df = None
            st.session_state.edit_log = []
            st.info("Run state reset.")

    col_c, col_d = st.columns(2)
    with col_c:
        animation_delay = st.slider("Seat animation delay (seconds)", min_value=0.1, max_value=1.5, value=0.35, step=0.05)
    with col_d:
        animate_requested = st.button("Animate Fill Until Pause", use_container_width=True)
        if animate_requested:
            if st.session_state.allocation_state is None:
                st.session_state.allocation_state = allocation_engine.initialize_state(students_df, subjects_df)

            placeholder = st.empty()
            while True:
                current_status = st.session_state.allocation_state.get("status")
                if current_status in {"paused", "completed"}:
                    break
                st.session_state.allocation_state = allocation_engine.run_next_group(
                    st.session_state.allocation_state
                )
                with placeholder.container():
                    _render_seat_status(st.session_state.allocation_state)
                if st.session_state.allocation_state.get("status") in {"paused", "completed"}:
                    break
                time.sleep(animation_delay)

            if st.session_state.allocation_state["status"] == "completed":
                st.session_state.allocated_df = allocation_engine.state_to_dataframe(st.session_state.allocation_state)
                st.success("Allocation completed successfully.")
            else:
                st.warning("Allocation paused for tie intervention.")

    if st.session_state.allocation_state is not None:
        _render_seat_status(st.session_state.allocation_state)

    if (
        st.session_state.allocation_state is not None
        and st.session_state.allocation_state.get("status") == "paused"
        and st.session_state.allocation_state.get("pending_tie") is not None
    ):
        pending = st.session_state.allocation_state["pending_tie"]
        st.error(
            f"Tie detected for subject {pending['subject_id']} at marks {pending['marks']}."
            f" Select {pending['seat_count']} winner(s) to continue."
        )
        candidate_df = _get_display_df(pd.DataFrame(pending["candidates"]))
        st.dataframe(candidate_df, use_container_width=True)
        if st.session_state.allocation_state.get("waitlisted_students"):
            st.warning("Tied students are temporarily marked as WAITLISTED until manual review.")
            waitlist_df = _get_display_df(pd.DataFrame(st.session_state.allocation_state["waitlisted_students"]))
            st.dataframe(waitlist_df, use_container_width=True)
        candidate_ids = [str(row["Student_ID"]) for row in pending["candidates"]]
        selected_winners = st.multiselect(
            "Select winning Student IDs",
            options=candidate_ids,
            default=candidate_ids[: pending["seat_count"]],
        )
        if st.button("Resolve Tie and Continue"):
            try:
                st.session_state.allocation_state = allocation_engine.apply_tie_resolution(
                    st.session_state.allocation_state,
                    selected_winners,
                )
                if st.session_state.allocation_state["status"] == "completed":
                    st.session_state.allocated_df = allocation_engine.state_to_dataframe(st.session_state.allocation_state)
                    st.success("Allocation completed successfully after tie resolution.")
                else:
                    st.warning("Another tie needs intervention.")
            except ValueError as tie_error:
                st.error(str(tie_error))

    if st.session_state.allocated_df is not None:
        allocated_df = st.session_state.allocated_df.copy()
        display_df = _get_display_df(allocated_df)

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                "Master Output",
                "Student View",
                "Subject View",
                "Department View",
                "Analytics Dashboard",
                "Manual Overrides",
            ]
        )

        with tab1:
            st.dataframe(display_df, use_container_width=True)
            csv_data = data_handler.export_data(display_df)
            st.download_button("Download Allocation CSV", data=csv_data, file_name="allocations.csv", mime="text/csv")
            excel_data = data_handler.export_excel_by_department(display_df)
            st.download_button(
                "Download Allocation Excel (Department Sheets)",
                data=excel_data,
                file_name="allocations_by_department.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        with tab2:
            search_id = st.text_input("Enter Student ID")
            if search_id:
                student_data = data_handler.get_student_info(display_df, search_id)
                if not student_data.empty:
                    st.dataframe(student_data, use_container_width=True)
                else:
                    st.warning("Student not found.")

        with tab3:
            subject_list = subjects_df['Subject_ID'].tolist()
            selected_subject = st.selectbox("Select Subject", subject_list)
            if selected_subject:
                subject_data = data_handler.get_subject_students(display_df, selected_subject)
                st.metric("Total Enrolled", len(subject_data))
                st.dataframe(subject_data, use_container_width=True)

        with tab4:
            dept_mapping = data_handler.get_department_mapping(display_df)
            st.dataframe(dept_mapping, use_container_width=True)

        with tab5:
            st.header("Allocation Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(visualizer.plot_allocation_status(display_df), use_container_width=True)
            
            with col2:
                st.plotly_chart(visualizer.plot_subject_popularity(display_df), use_container_width=True)
                
            st.plotly_chart(visualizer.plot_department_distribution(display_df), use_container_width=True)

        with tab6:
            st.subheader("Post-allocation Manual Reassignment")
            override_student_id = st.selectbox(
                "Select Student ID",
                options=allocated_df["Student_ID"].astype(str).tolist(),
            )
            override_subject = st.selectbox(
                "Reassign Subject",
                options=[allocation_engine.unallocated_label] + subjects_df["Subject_ID"].astype(str).tolist(),
            )
            force_override = st.checkbox("Force override when seat is full")
            if st.button("Apply Reassignment"):
                updated_df, message, is_error = _apply_manual_override(
                    st.session_state.allocated_df,
                    override_student_id,
                    override_subject,
                    subjects_df,
                    force_override,
                )
                if is_error:
                    st.error(message)
                else:
                    st.session_state.allocated_df = updated_df
                    st.session_state.edit_log.append(
                        {
                            "Student_ID": override_student_id,
                            "New_Subject": override_subject,
                            "Force_Override": force_override,
                        }
                    )
                    st.success(message)

            if st.session_state.edit_log:
                st.caption("Manual override audit log")
                st.dataframe(pd.DataFrame(st.session_state.edit_log), use_container_width=True)

else:
    st.info("Please upload both CSV files in the sidebar to proceed.")