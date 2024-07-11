import streamlit as st
import boto3
import json
import requests

# Specify your AWS region
aws_region = "eu-north-1"

# Initialize the SageMaker runtime client with the specified region
runtime = boto3.client('sagemaker-runtime', region_name=aws_region)

# Function to get prediction from the endpoint
def get_prediction(data, endpoint_url):
    headers = {"Content-Type": "application/json"}
    response = requests.post(endpoint_url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}

# Streamlit app
st.title("Stock Forecasting Application")

# Input data
data = st.text_area("Enter your data (JSON format):")

# Select forecast term
term = st.selectbox("Select Forecast Term", ["Short Term (7 days)", "Long Term (Annually)"])

if st.button("Predict"):
    try:
        input_data = json.loads(data)  # Parse the JSON input
        if term == "Short Term (7 days)":
            endpoint_url = "https://runtime.sagemaker.eu-north-1.amazonaws.com/endpoints/canvas-shortterm/invocations"
        elif term == "Long Term (Annually)":
            endpoint_url = "https://runtime.sagemaker.eu-north-1.amazonaws.com/endpoints/canvas-new-deployment-07-11-2024-2-00-AM/invocations"

        result = get_prediction(input_data, endpoint_url)
        st.write("Prediction Result:", result)
    except json.JSONDecodeError:
        st.error("Invalid JSON format. Please check your input.")
