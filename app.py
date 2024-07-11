import streamlit as st
import boto3
import json

# Initialize the SageMaker runtime client
runtime = boto3.client('runtime.sagemaker')

# Function to get prediction from the endpoint
def get_prediction(data, endpoint_name):
    response = runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=json.dumps(data)
    )
    result = json.loads(response['Body'].read().decode())
    return result

# Streamlit app
st.title("Stock Forecasting Application")

# Input data
data = st.text_input("Enter your data:")

# Select forecast term
term = st.selectbox("Select Forecast Term", ["Short Term (7 days)", "Long Term (Annually)"])

if st.button("Predict"):
    if term == "Short Term (7 days)":
        endpoint_name = "https://runtime.sagemaker.eu-north-1.amazonaws.com/endpoints/canvas-shortterm/invocations"  # Replace with your endpoint name
    elif term == "Long Term (Annually)":
        endpoint_name = "https://runtime.sagemaker.eu-north-1.amazonaws.com/endpoints/canvas-new-deployment-07-11-2024-2-00-AM/invocations"  # Replace with your endpoint name

    result = get_prediction(data, endpoint_name)
    st.write("Prediction Result:", result)
