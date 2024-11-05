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

# Cache function to fetch and load the dataset from a GitHub URL
@st.cache_data
def fetch_and_load_data_from_github(url):
    response = requests.get(url)
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name
        df, meta = pyreadstat.read_xport(tmp_file_path)
        return df
    else:
        st.error("Failed to fetch data from GitHub. Please check the URL.")
        return None

# Streamlit app

    
def main():
    # Set custom CSS for the background image and layout spacing
    st.markdown(
        """
        <style>
        body {
            background-image: url("https://example.com/path-to-your-image.jpg");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }
        .reportview-container {
            background: transparent; /* Ensure content background is transparent to show background image */
        }
        /* Move columns to edges of the screen */
        .left-column {
            position: fixed;
            left: 20px;
            top: 100px;
            width: 200px;
        }
        .right-column {
            position: fixed;
            right: 20px;
            top: 100px;
            width: 200px;
        }
        .center-column {
            margin-left: 250px;
            margin-right: 250px;
        }
        </style>
        ,
        
        unsafe_allow_html=True
        """
    )

    st.title("ADSL Subject-Level Streamlit App")
    
    # Define layout columns with CSS classes for position adjustments
    left_column = st.container()
    center_column = st.container()
    right_column = st.container()

    with left_column:
        st.markdown('<div class="left-column">', unsafe_allow_html=True)
        # Subject Data Selection
        st.subheader("Select Subject Data")
        subject_choices = {
            "Age": "AGE",
            "Baseline BMI": "BMIBL",
            "Baseline Height": "HEIGHTBL",
            "Baseline Weight": "WEIGHTBL",
            "Years of Education": "EDUCLVL"
        }
        
        selected_subject = st.selectbox("Select Subject Data", options=list(subject_choices.keys()))
        st.markdown('</div>', unsafe_allow_html=True)

    with center_column:
        st.markdown('<div class="center-column">', unsafe_allow_html=True)
        # Placeholder for the plot
        st.subheader("Boxplot Visualization")
        fig_placeholder = st.empty()  # Placeholder for the boxplot
        st.markdown('</div>', unsafe_allow_html=True)

    with right_column:
        st.markdown('<div class="right-column">', unsafe_allow_html=True)
        # File uploader
        st.subheader("Upload ADSL Data or Fetch from GitHub")
        uploaded_file = st.file_uploader("Upload ADSL .xpt file", type="xpt")

        # Button to load default dataset from GitHub
        github_url = st.text_input("GitHub Raw URL for ADSL .xpt file", 
                                    "https://raw.githubusercontent.com/rejipmathew/ADSL_streamlit/main/ADSL.XPT")
        
        if st.button("Load from GitHub"):
            adsl_data = fetch_and_load_data_from_github(github_url)
            if adsl_data is None:
                st.warning("Failed to load data from GitHub.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Load data and generate plot after file is uploaded or fetched from GitHub
    if uploaded_file is not None:
        # Load data from uploaded file
        adsl_data = load_adsl_data(uploaded_file)

    # If data is loaded, display it and create plot
    if 'adsl_data' in locals() and adsl_data is not None:
        # Display dataframe preview
        st.write("ADSL Data Preview:")
        st.dataframe(adsl_data.head())

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
            # Display the figure in the center column
            fig_placeholder.plotly_chart(fig)
        else:
            fig_placeholder.warning(f"{selected_subject} column not found in the data.")

# Run the app
if __name__ == "__main__":
    main()
