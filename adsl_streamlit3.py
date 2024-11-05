import streamlit as st
import pandas as pd
import pyreadstat
import tempfile
import requests
import plotly.express as px

# Predefined GitHub URL for ADSL .xpt file
GITHUB_URL = "https://raw.githubusercontent.com/rejipmathew/ADSL_streamlit/main/ADSL.XPT"

# Function to load ADSL data from .xpt file
def load_adsl_data(file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(file.read())
        tmp_file_path = tmp_file.name
    df, meta = pyreadstat.read_xport(tmp_file_path)
    return df

# Cached function to fetch the dataset from a predefined GitHub URL
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_data_from_github():
    response = requests.get(GITHUB_URL)
    if response.status_code == 200:
        return response.content
    else:
        st.error("Failed to fetch data from GitHub.")
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

    # Sidebar for navigation with "Visualization" as the default option
    page = st.sidebar.radio("Navigation", ["Data Preview", "Visualization"], index=1)

    # File uploader
    uploaded_file = st.sidebar.file_uploader("Upload ADSL .xpt file", type="xpt")
    
    # Load data from GitHub and cache it
    if st.sidebar.button("Load from GitHub"):
        data_content = fetch_data_from_github()
        if data_content:
            # Create a temporary file for the downloaded content
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(data_content)
            temp_file.seek(0)  # Reset file pointer for reading later
            # Load the ADSL data and cache it
            adsl_data = load_adsl_data(temp_file)
            st.session_state.adsl_data = adsl_data  # Store the data in session state

    # Load data from uploaded file if available
    if uploaded_file is not None:
        adsl_data = load_adsl_data(uploaded_file)
        st.session_state.adsl_data = adsl_data  # Store the data in session state

    # Render selected page if data is available
    if 'adsl_data' in st.session_state:
        adsl_data = st.session_state.adsl_data

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
                
                # Set background to transparent white and text color to black
                fig.update_layout(
                    paper_bgcolor="rgba(255, 255, 255, 0.5)",  # Outer background transparent white
                    plot_bgcolor="rgba(255, 255, 255, 0.5)",    # Inner plot background transparent white
                    font=dict(color="black"),  # Set all text elements to black
                    legend=dict(
                        orientation="h",
                        x=0.5,
                        xanchor="center",
                        y=-0.2  # Position below the plot
                    )
                )
                
                st.plotly_chart(fig)
            else:
                st.warning(f"{selected_subject} column not found in the data.")
    else:
        st.info("Please upload an ADSL .xpt file or load one from GitHub.")

# Run the app
if __name__ == "__main__":
    main()
