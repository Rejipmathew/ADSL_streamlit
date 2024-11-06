import streamlit as st
import pandas as pd
import pyreadstat
import tempfile
import requests
import plotly.express as px
from lifelines import KaplanMeierFitter
import plotly.graph_objs as go

# Function to load data from a .xpt file
def load_data(file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(file.read())
        tmp_file_path = tmp_file.name
    df, _ = pyreadstat.read_xport(tmp_file_path)
    return df

# Function to fetch the dataset from a GitHub URL with enhanced error handling
def fetch_data_from_github(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        # Verify that the content type is as expected for an XPT file
        if 'application/octet-stream' in response.headers['Content-Type']:
            return response.content
        else:
            st.error("The URL did not return a valid XPT file. Please check the file format and try again.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data from GitHub: {e}")
        return None

# Function to load data from the GitHub content fetched
def load_data_from_github(content):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xpt') as tmp_file:
            tmp_file.write(content)
            tmp_file.seek(0)  # Reset file pointer for reading
            return load_data(tmp_file)
    except Exception as e:
        st.error(f"Failed to load data from GitHub content: {e}")
        return None

# Function to create KM plot
def km_plot(adsl, adtte):
    anl = adsl[
        (adsl['SAFFL'] == "Y") & (adsl['STUDYID'] == "CDISCPILOT01")
    ][['STUDYID', 'USUBJID', 'TRT01A']].merge(
        adtte[adtte['STUDYID'] == "CDISCPILOT01"][['STUDYID', 'USUBJID', 'AVAL', 'CNSR', 'PARAM', 'PARAMCD']],
        on=['STUDYID', 'USUBJID'],
        how='inner'
    ).assign(
        TRT01A=lambda x: pd.Categorical(x['TRT01A'], categories=["Placebo", "Xanomeline Low Dose", "Xanomeline High Dose"]),
        AVAL=lambda x: x['AVAL'] / 30.4167  # Convert AVAL to months
    )
    
    if len(anl) <= 5:
        st.error("Not enough observations for this selection. Modify filters and try again.")
        return None
    
    kmf = KaplanMeierFitter()
    fig = go.Figure()
    
    for treatment in anl['TRT01A'].cat.categories:
        treatment_data = anl[anl['TRT01A'] == treatment]
        kmf.fit(treatment_data['AVAL'], event_observed=treatment_data['CNSR'], label=treatment)
        fig.add_trace(go.Scatter(
            x=kmf.survival_function_.index,
            y=kmf.survival_function_[treatment],
            mode='lines+markers',
            name=treatment,
            hoverinfo='text',
            text=kmf.survival_function_[treatment].apply(lambda x: f'Survival Probability: {x:.2%}'),
        ))
    
    fig.update_layout(
        title="KM plot for Time to First Dermatologic Event: Safety population",
        xaxis_title="Time (Months)",
        yaxis_title="Survival Probability (%)",
        legend_title="Treatment",
        yaxis=dict(range=[0, 1]),
    )
    
    fig.add_shape(type="line", x0=0, y0=0.5, x1=1, y1=0.5, line=dict(color="gray", dash="dash"))
    return fig

# Streamlit app
def main():
    # Initialize session state for data storage if it does not exist
    if "adsl_data" not in st.session_state:
        st.session_state.adsl_data = None
    if "adtte_data" not in st.session_state:
        st.session_state.adtte_data = None

    st.title("Demographics and KP-Curve CDISC Visualization")

    # Sidebar navigation with radio buttons
    nav_option = st.sidebar.radio("Select an option", ["Instructions", "Upload Files", "Raw Data", "Visualization", "Kaplan-Meier Curve"])

    # Instructions page as the default
    if nav_option == "Instructions":
        st.subheader("Instructions for Using the App")
        st.write("""
        Welcome to the Demographics and KP-Curve CDISC Visualization App!
        (Note: Use top '>' to see the option button in mobile app)
        **Instructions:**
        1. **Upload Files**: You can upload your own ADSL and ADTTE files in XPT format, or load them directly from a GitHub repository.
        2. **Raw Data**: View the raw data from the uploaded files.
        3. **Visualization**: Create a boxplot visualization for different subject data like Age, Baseline BMI, etc., across different treatment groups.
        4. **Kaplan-Meier Curve**: Generate a Kaplan-Meier survival curve for the treatment groups based on the data you have uploaded.

        The app supports two ways of uploading data:
        - By uploading the files manually.
        - By fetching the data from GitHub using the provided URLs.

        **Important Notes**:
        - Make sure to upload both the ADSL and ADTTE data for the Kaplan-Meier curve to work.
        - Ensure the data is from the same study for the analysis to be valid.

        Use the options in the sidebar to navigate between different sections of the app.
        """)
        return

    # Display file upload section only in the "Upload Files" page
    if nav_option == "Upload Files":
        st.subheader("Upload ADSL and ADTTE Files")

                # Load data from GitHub if the button is clicked
        if st.button("Load ADSL from GitHub"):
            adsl_data_content = fetch_data_from_github(github_adsl_url)
            if adsl_data_content:
                st.session_state.adsl_data = load_data_from_github(adsl_data_content)

        if st.button("Load ADTTE from GitHub"):
            adtte_data_content = fetch_data_from_github(github_adtte_url)
            if adtte_data_content:
                st.session_state.adtte_data = load_data_from_github(adtte_data_content)
                
        # GitHub URL input for ADSL and ADTTE data
        github_adsl_url = st.text_input("GitHub URL for ADSL .xpt file", 
                                      "https://raw.githubusercontent.com/rejipmathew/ADSL_streamlit/main/ADSL.XPT")
        github_adtte_url = st.text_input("GitHub URL for ADTTE .xpt file", 
                                       "https://raw.githubusercontent.com/rejipmathew/ADSL_streamlit/main/ADTTE.XPT")
        
        # File upload for ADSL and ADTTE
        adsl_file = st.file_uploader("Upload ADSL .xpt file", type="xpt", key='adsl')
        adtte_file = st.file_uploader("Upload ADTTE .xpt file", type="xpt", key='adtte')



        # Load ADSL and ADTTE data from uploaded files
        if adsl_file is not None:
            st.session_state.adsl_data = load_data(adsl_file)
        if adtte_file is not None:
            st.session_state.adtte_data = load_data(adtte_file)

    # Render content based on selected navigation option
    if nav_option == "Raw Data":
        st.subheader("Raw Data Preview")
        if st.session_state.adsl_data is not None and st.session_state.adtte_data is not None:
            st.write("ADSL Data:")
            st.dataframe(st.session_state.adsl_data.head())
            st.write("ADTTE Data:")
            st.dataframe(st.session_state.adtte_data.head())
        else:
            st.warning("Please upload or load both ADSL and ADTTE data.")

    elif nav_option == "Visualization":
        st.subheader("Boxplot Visualization")
        if st.session_state.adsl_data is not None:
            subject_choices = {
                "Age": "AGE",
                "Baseline BMI": "BMIBL",
                "Baseline Height": "HEIGHTBL",
                "Baseline Weight": "WEIGHTBL",
                "Years of Education": "EDUCLVL"
            }
            
            selected_subject = st.selectbox("Select Subject Data", options=list(subject_choices.keys()))

            if selected_subject and subject_choices[selected_subject] in st.session_state.adsl_data.columns:
                subject_column = subject_choices[selected_subject]

                # Define colors for treatment groups
                treatment_colors = {
                    'Placebo': 'blue',
                    'Xanomeline Low Dose': 'green',
                    'Xanomeline High Dose': 'purple'
                }

                # Generate boxplot using Plotly
                fig_box = px.box(
                    st.session_state.adsl_data, 
                    x='TRT01A', 
                    y=subject_column, 
                    title=f"{selected_subject} by Treatment Groups",
                    labels={subject_column: selected_subject, 'TRT01A': 'Treatment'},
                    color='TRT01A',  
                    color_discrete_map=treatment_colors,
                    points='all'
                )
                fig_box.update_layout(plot_bgcolor='rgba(255, 255, 255, 0.5)')  # Transparent white background
                st.plotly_chart(fig_box)
        else:
            st.warning("Please upload or load ADSL data.")

    elif nav_option == "Kaplan-Meier Curve":
        st.subheader("Kaplan-Meier Curve")
        if st.session_state.adsl_data is not None and st.session_state.adtte_data is not None:
            fig_km = km_plot(st.session_state.adsl_data, st.session_state.adtte_data)
            if fig_km:
                st.plotly_chart(fig_km)
        else:
            st.warning("Please upload or load both ADSL and ADTTE data.")

if __name__ == "__main__":
    main()
