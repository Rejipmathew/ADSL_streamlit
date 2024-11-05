import streamlit as st
import pandas as pd
import pyreadstat
import tempfile
import requests
import plotly.express as px

# Function to load ADSL data from .xpt file
def load_adsl_data(file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(file.read())
        tmp_file_path = tmp_file.name
    df, meta = pyreadstat.read_xport(tmp_file_path)
    return df

# Function to fetch the dataset from a GitHub URL
def fetch_data_from_github(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        st.error("Failed to fetch data from GitHub. Please check the URL.")
        return None

# Streamlit app
def main():
    # Set custom CSS for the background color and column spacing
    st.markdown(
        """
    <style>
    .reportview-container .markdown-text-container { font-family: monospace; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    .Widget>label { color: white; font-family: monospace; }
    [class^="st-b"]  { color: white; font-family: monospace; }
    .st-bb { background-color: transparent; }
    .st-at { background-color: #0c0080; }
    footer { font-family: monospace; }
    .reportview-container .main footer, .reportview-container .main footer a { color: #0c0080; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("ADSL Subject-Level Streamlit App")

    # Sidebar for navigation
    page = st.sidebar.radio("Navigation", ["Data Preview", "Visualization"])

    # File uploader
    uploaded_file = st.sidebar.file_uploader("Upload ADSL .xpt file", type="xpt")
    github_url = st.sidebar.text_input("GitHub Raw URL for ADSL .xpt file",
                                       "https://raw.githubusercontent.com/rejipmathew/ADSL_streamlit/main/ADSL.XPT")
    
    if st.sidebar.button("Load from GitHub"):
        data_content = fetch_data_from_github(github_url)
        if data_content:
            uploaded_file = tempfile.NamedTemporaryFile(delete=False)
            uploaded_file.write(data_content)
            uploaded_file.seek(0)  # Reset file pointer for reading later

    # Load data and render selected page
    if uploaded_file is not None:
        adsl_data = load_adsl_data(uploaded_file)

        # Data Preview Page
        if page == "Data Preview":
            st.header("ADSL Data Preview")
            st.write("Showing the first few rows of the ADSL dataset.")
            st.dataframe(adsl_data.head())

        # Visualization Page
        elif page == "Visualization":
            st.header("Boxplot Visualization")
            subject_choices = {
                "Age": "AGE",
                "Baseline BMI": "BMIBL",
                "Baseline Height": "HEIGHTBL",
                "Baseline Weight": "WEIGHTBL",
                "Years of Education": "EDUCLVL"
            }
            
            selected_subject = st.selectbox("Select Subject Data", options=list(subject_choices.keys()))

            if selected_subject and subject_choices[selected_subject] in adsl_data.columns:
                subject_column = subject_choices[selected_subject]
                
                # Define colors for treatment groups
                treatment_colors = {
                    'Group 1': 'blue',
                    'Group 2': 'green',
                    'Group 3': 'red'
                }

                # Generate boxplot using Plotly
                fig = px.box(
                    adsl_data, 
                    x='TRT01A', 
                    y=subject_column, 
                    title=f"{selected_subject} by Treatment Groups",
                    labels={subject_column: selected_subject, 'TRT01A': 'Treatment'},
                    color='TRT01A',  # Color by treatment group
                    color_discrete_map=treatment_colors,  # Map treatments to colors
                    points='all'  # Show all data points
                )
                st.plotly_chart(fig)
            else:
                st.warning(f"{selected_subject} column not found in the data.")
    else:
        st.info("Please upload an ADSL .xpt file or load one from GitHub.")

# Run the app
if __name__ == "__main__":
    main()
