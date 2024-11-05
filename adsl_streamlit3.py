import streamlit as st
import pandas as pd
import pyreadstat
import tempfile
import requests
import plotly.express as px
import plotly.figure_factory as ff

# Predefined GitHub URLs for ADSL and ADTTE .xpt files
GITHUB_ADSL_URL = "https://raw.githubusercontent.com/rejipmathew/ADSL_streamlit/main/ADSL.XPT"
GITHUB_ADTTE_URL = "https://raw.githubusercontent.com/rejipmathew/ADSL_streamlit/main/ADTTE.XPT"

# Function to load data from .xpt file
def load_data(file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(file.read())
        tmp_file_path = tmp_file.name
    df, meta = pyreadstat.read_xport(tmp_file_path)
    return df

# Cached function to fetch the dataset from a predefined GitHub URL
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_data_from_github(url):
    response = requests.get(url)
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

    # Sidebar for navigation with options
    page = st.sidebar.radio("Navigation", ["Data Preview", "Visualization", "KP Curve"], index=1)

    # File uploaders for ADSL and ADTTE
    uploaded_adsl_file = st.sidebar.file_uploader("Upload ADSL .xpt file", type="xpt", key="adsl")
    uploaded_adtte_file = st.sidebar.file_uploader("Upload ADTTE .xpt file", type="xpt", key="adtte")
    
    # Load data from GitHub and cache it
    if st.sidebar.button("Load ADSL from GitHub"):
        adsl_data_content = fetch_data_from_github(GITHUB_ADSL_URL)
        if adsl_data_content:
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(adsl_data_content)
            temp_file.seek(0)
            adsl_data = load_data(temp_file)
            st.session_state.adsl_data = adsl_data  # Store the ADSL data in session state

    if st.sidebar.button("Load ADTTE from GitHub"):
        adtte_data_content = fetch_data_from_github(GITHUB_ADTTE_URL)
        if adtte_data_content:
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(adtte_data_content)
            temp_file.seek(0)
            adtte_data = load_data(temp_file)
            st.session_state.adtte_data = adtte_data  # Store the ADTTE data in session state

    # Load data from uploaded files if available
    if uploaded_adsl_file is not None:
        adsl_data = load_data(uploaded_adsl_file)
        st.session_state.adsl_data = adsl_data  # Store the ADSL data in session state

    if uploaded_adtte_file is not None:
        adtte_data = load_data(uploaded_adtte_file)
        st.session_state.adtte_data = adtte_data  # Store the ADTTE data in session state

    # Render selected page if data is available
    if 'adsl_data' in st.session_state and 'adtte_data' in st.session_state:
        adsl_data = st.session_state.adsl_data
        adtte_data = st.session_state.adtte_data

        # Data Preview Page
        if page == "Data Preview":
            st.header("ADSL Data Preview")
            st.write("Showing the first few rows of the ADSL dataset.")
            st.dataframe(adsl_data.head())
            
            st.header("ADTTE Data Preview")
            st.write("Showing the first few rows of the ADTTE dataset.")
            st.dataframe(adtte_data.head())

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
                
                # Set custom background image for the plot
                fig.update_layout(
                    paper_bgcolor="rgba(255, 255, 255, 0.5)",  # Outer background transparent white
                    plot_bgcolor="rgba(255, 255, 255, 0.5)",    # Inner plot background transparent white
                    font=dict(color="black"),  # Set all text elements to black
                    legend=dict(
                        orientation="h",
                        x=0.5,
                        xanchor="center",
                        y=-0.2  # Position below the plot
                    ),
                    images=[
                        dict(
                            source="https://path/to/your/image.jpg",  # Replace with your image URL
                            xref="paper", yref="paper",
                            x=0.5, y=0.5,
                            sizex=1, sizey=1,
                            opacity=0.2,  # Adjust opacity for better visibility of the plot
                            layer="below"
                        )
                    ]
                )
                
                st.plotly_chart(fig)
            else:
                st.warning(f"{selected_subject} column not found in the data.")

        # KP Curve Page
        elif page == "KP Curve":
            st.header("Kaplan-Meier Curve Visualization")
            
            # Check if relevant columns exist in ADTTE dataset
            if 'ADTTE' in adtte_data.columns and 'CNSR' in adtte_data.columns:
                # Prepare data for KM curve
                km_data = adtte_data[['ADTTE', 'CNSR']].dropna()

                # Create Kaplan-Meier curve using Plotly
                fig_km = ff.create_kaplan_meier(km_data, 
                                                  time_column='ADTTE', 
                                                  event_column='CNSR', 
                                                  title="Kaplan-Meier Survival Curve")
                
                # Update layout for better readability
                fig_km.update_layout(
                    plot_bgcolor="rgba(255, 255, 255, 0.5)",  # Transparent white background
                    font=dict(color="black")  # Black font color for text
                )
                
                st.plotly_chart(fig_km)
            else:
                st.warning("Required columns for Kaplan-Meier curve not found in ADTTE data.")

    else:
        st.info("Please upload both ADSL and ADTTE .xpt files or load them from GitHub.")

# Run the app
if __name__ == "__main__":
    main()
