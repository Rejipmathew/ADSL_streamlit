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

# Cached function to fetch and load dataset directly from a GitHub URL
@st.cache_data
def load_data_from_github(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError if the status is not 200
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xpt') as tmp_file:
            tmp_file.write(response.content)
            tmp_file.seek(0)  # Reset file pointer for reading
            df, _ = pyreadstat.read_xport(tmp_file.name)
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data from GitHub: {e}")
        return None

# Function to create KM plot
def km_plot(adsl, adtte):
    anl = adsl[
        (adsl['SAFFL'] == "Y") & (adsl['STUDYID'] == "CDISCPILOT01")
    ][['STUDYID', 'USUBJID', 'TRT01A']].merge(
        adtte[
            adtte['STUDYID'] == "CDISCPILOT01"
        ][['STUDYID', 'USUBJID', 'AVAL', 'CNSR', 'PARAM', 'PARAMCD']],
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
    st.title("ADSL and ADTTE Data Visualization App")
    
    # Sidebar for navigation
    page = st.sidebar.radio("Navigation", ["Upload Data", "Raw Data", "Visualization", "Kaplan-Meier Curve"])
    
    # Page for uploading data
    if page == "Upload Data":
        st.subheader("Upload ADSL and ADTTE Datasets")
        
        # File uploader for ADSL and ADTTE data
        adsl_file = st.file_uploader("Upload ADSL .xpt file", type="xpt", key='adsl')
        adtte_file = st.file_uploader("Upload ADTTE .xpt file", type="xpt", key='adtte')

        # GitHub URL input for ADSL and ADTTE data
        github_adsl_url = st.text_input("GitHub URL for ADSL .xpt file", 
                                        "https://raw.githubusercontent.com/rejipmathew/ADSL_streamlit/main/ADSL.XPT")
        github_adtte_url = st.text_input("GitHub URL for ADTTE .xpt file", 
                                         "https://raw.githubusercontent.com/rejipmathew/ADSL_streamlit/main/ADTTE.XPT")
        
        # Load data based on the input method
        global adsl_data, adtte_data
        adsl_data, adtte_data = None, None

        # Load data from GitHub if the button is clicked
        if st.button("Load ADSL from GitHub"):
            adsl_data = load_data_from_github(github_adsl_url)

        if st.button("Load ADTTE from GitHub"):
            adtte_data = load_data_from_github(github_adtte_url)

        # Load ADSL and ADTTE data from uploaded files
        if adsl_file is not None:
            adsl_data = load_data(adsl_file)
        if adtte_file is not None:
            adtte_data = load_data(adtte_file)

        if adsl_data is not None and adtte_data is not None:
            st.success("Data loaded successfully!")
    
    # Page for displaying raw data
    elif page == "Raw Data":
        st.subheader("Raw Data Preview")
        
        if 'adsl_data' in globals() and 'adtte_data' in globals() and adsl_data is not None and adtte_data is not None:
            st.write("ADSL Data:")
            st.dataframe(adsl_data.head())
            st.write("ADTTE Data:")
            st.dataframe(adtte_data.head())
        else:
            st.warning("No data loaded. Please go to 'Upload Data' and load the datasets first.")
    
    # Page for boxplot visualization
    elif page == "Visualization":
        st.subheader("Boxplot Visualization")
        
        if 'adsl_data' in globals() and adsl_data is not None:
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
                    'Placebo': 'blue',
                    'Xanomeline Low Dose': 'green',
                    'Xanomeline High Dose': 'red'
                }

                # Generate boxplot using Plotly
                fig_box = px.box(
                    adsl_data, 
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
            st.warning("No ADSL data loaded. Please go to 'Upload Data' and load the datasets first.")
    
    # Page for Kaplan-Meier plot
    elif page == "Kaplan-Meier Curve":
        st.subheader("Kaplan-Meier Curve")
        
        if 'adsl_data' in globals() and 'adtte_data' in globals() and adsl_data is not None and adtte_data is not None:
            km_fig = km_plot(adsl_data, adtte_data)
            if km_fig is not None:
                st.plotly_chart(km_fig)
        else:
            st.warning("No data loaded. Please go to 'Upload Data' and load the datasets first.")

# Run the app
if __name__ == "__main__":
    main()
