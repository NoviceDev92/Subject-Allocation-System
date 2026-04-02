import streamlit as st
from data_handler import load_data, get_student_info, get_subject_students, get_department_mapping, export_data
from allocator import allocate
from visualizer import plot_allocation_status, plot_subject_popularity, plot_department_distribution

st.set_page_config(page_title="Course Allocation System", layout="wide")

st.title("Merit-Based Course Allocation System")

with st.sidebar:
    st.header("Data Input")
    students_file = st.file_uploader("Upload Students CSV", type=["csv"])
    subjects_file = st.file_uploader("Upload Subjects CSV", type=["csv"])

if students_file and subjects_file:
    students_df = load_data(students_file)
    subjects_df = load_data(subjects_file)

    if 'allocated_df' not in st.session_state:
        st.session_state.allocated_df = None

    if st.button("Run Allocation Algorithm"):
        st.session_state.allocated_df = allocate(students_df, subjects_df)
        st.success("Allocation completed successfully!")

    if st.session_state.allocated_df is not None:
        allocated_df = st.session_state.allocated_df

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Master Output", "Student View", "Subject View", "Department View", "Analytics Dashboard"])

        with tab1:
            st.dataframe(allocated_df, use_container_width=True)
            csv_data = export_data(allocated_df)
            st.download_button("Download Allocation CSV", data=csv_data, file_name="allocations.csv", mime="text/csv")

        with tab2:
            search_id = st.text_input("Enter Student ID")
            if search_id:
                student_data = get_student_info(allocated_df, search_id)
                if not student_data.empty:
                    st.dataframe(student_data, use_container_width=True)
                else:
                    st.warning("Student not found.")

        with tab3:
            subject_list = subjects_df['Subject_ID'].tolist()
            selected_subject = st.selectbox("Select Subject", subject_list)
            if selected_subject:
                subject_data = get_subject_students(allocated_df, selected_subject)
                st.metric("Total Enrolled", len(subject_data))
                st.dataframe(subject_data, use_container_width=True)

        with tab4:
            dept_mapping = get_department_mapping(allocated_df)
            st.dataframe(dept_mapping, use_container_width=True)

        with tab5:
            st.header("Allocation Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(plot_allocation_status(allocated_df), use_container_width=True)
            
            with col2:
                st.plotly_chart(plot_subject_popularity(allocated_df), use_container_width=True)
                
            st.plotly_chart(plot_department_distribution(allocated_df), use_container_width=True)

else:
    st.info("Please upload both CSV files in the sidebar to proceed.")