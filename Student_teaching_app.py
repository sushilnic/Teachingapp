import streamlit as st
import pandas as pd
import time
import sqlite3
from streamlit.proto.Progress_pb2 import Progress as ProgressProto
# SQLite connection for progress tracking
conn = sqlite3.connect("student_progress.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS progress (user TEXT, question_id INT)")

# App title
st.sidebar.title("Student Teaching App")
st.title("Student Teaching App")
st.write("Select filters, and solve interactively.")

# Session state for tracking progress
if "solved" not in st.session_state:
    st.session_state.solved = []

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload Questions File (CSV/Excel)", type=["csv", "xlsx"])
data = None

if uploaded_file:
    try:
        # Read file
        if uploaded_file.name.endswith(".csv"):
            data = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            data = pd.read_excel(uploaded_file)

        # Validate structure
        required_columns = ["Question", "Answer", "Chapter", "Exercise", "Language", "Difficulty"]
        if not all(col in data.columns for col in required_columns):
            st.sidebar.error(f"Uploaded file must contain columns: {', '.join(required_columns)}")
        else:
            st.sidebar.success("File uploaded and validated successfully!")
    except Exception as e:
        st.error(f"Error reading file: {e}")

# Language selection
language = st.sidebar.radio("Select Language", data["Language"].unique() if data is not None else [])

# Chapter and exercise selection
chapter = st.sidebar.selectbox("Select Chapter", data["Chapter"].unique() if data is not None else [])
exercise = st.sidebar.selectbox("Select Exercise", data["Exercise"].unique() if data is not None else [])

# Difficulty level
difficulty = st.sidebar.selectbox("Select Difficulty Level", data["Difficulty"].unique() if data is not None else [])

# Filter data
if data is not None:
    filtered_data = data[
        (data["Language"] == language) &
        (data["Chapter"] == chapter) &
        (data["Exercise"] == exercise) &
        (data["Difficulty"] == difficulty)
    ]

    if not filtered_data.empty:
        st.write(f"Showing questions for Chapter: {chapter}, Exercise: {exercise}, Difficulty: {difficulty}")

        for idx, row in filtered_data.iterrows():
            if idx in st.session_state.solved:
                continue  # Skip already solved questions
            
            st.markdown(f"### Q{idx+1}: {row['Question']}")
            
            # Display LaTeX equations if available
            if "LatexEquation" in row and pd.notna(row["LatexEquation"]):
                st.latex(row["LatexEquation"])
            
            # Display image if available
            if "Image" in row and pd.notna(row["Image"]):
                st.image(row["Image"], caption=f"Diagram for Q{idx+1}")

            # Solve button
            if st.button(f"Solve Q{idx+1}", key=idx):
                st.write(f"**Answer:** {row['Answer']}")
                st.session_state.solved.append(idx)
                c.execute("INSERT INTO progress (user, question_id) VALUES (?, ?)", ("user1", idx))
                conn.commit()
                st.success("Question marked as solved.")
                st.rerun()  # Reload to reflect progress
    else:
        st.warning("No questions found for the selected filters.")

# Clear selection button
if st.sidebar.button("Clear Selection"):
    chapter, exercise, difficulty = None, None, None
    st.rerun()

# Progress tracking
st.write("### Progress")
total_questions = len(filtered_data) if data is not None else 0
solved_questions = len(st.session_state.solved)
st.write(f"Questions Solved: {solved_questions}/{total_questions}")
int progress = solved_questions / total_questions if total_questions else 0
st.progress(progress)

# Export progress
if st.button("Export Progress"):
    progress_data = pd.DataFrame(st.session_state.solved, columns=["Solved Questions"])
    progress_data.to_csv("progress.csv", index=False)
    st.success("Progress exported successfully!")

# Gamification
if solved_questions >= 5:
    st.balloons()
    st.success("Congratulations! You've earned the Bronze Badge.")

# Timer for practice
if st.button("Start 10-Second Timer"):
    for i in range(10, 0, -1):
        st.write(f"Time left: {i} seconds")
        time.sleep(1)
    st.write("Time's up!")

# Theme toggle
theme = st.sidebar.radio("Select Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        """
        <style>
        body {
            background-color: #333333;
            color: #ffffff;
        }
        </style>
        """, unsafe_allow_html=True
      )
