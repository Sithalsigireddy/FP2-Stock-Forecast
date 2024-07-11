import streamlit as st
import boto3
import pandas as pd
import io
 
# Define the SageMaker endpoint names and regions
SHORT_TERM_ENDPOINT_NAME = "canvas-shortterm"  # Short-term endpoint name
LONG_TERM_ENDPOINT_NAME = "canvas-new-deployment-07-11-2024-2-00-AM"  # Long-term endpoint name
AWS_REGION = "eu-north-1"  # Specify your AWS region
 
# Local path where the downloaded file is saved
local_file_path = 'newprocessed_TATAMOTORS.NS_stock_data.csv'
 
# Function to call the SageMaker endpoint
def get_forecast_from_sagemaker(data, endpoint_name, aws_region):
    client = boto3.client("runtime.sagemaker", region_name=aws_region)
    body = data.to_csv(index=False).encode("utf-8")
    try:
        response = client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="text/csv",
            Body=body,
            Accept="text/csv"
        )
        result = response['Body'].read().decode('utf-8')
        # Parse the CSV response
        result_df = pd.read_csv(io.StringIO(result))
        return result_df
    except client.exceptions.ModelError as e:
        st.error(f"Model error: {e}")
        return None
    except Exception as e:
        st.error(f"Error invoking endpoint: {e}")
        return None
 
# Streamlit interface
st.title("Forecast Tata Motors Stock")
 
# Information about forecast types
st.info("Select 'Short Term' for a 7-day forecast or 'Long Term' for a 365-day forecast.")
 
# Dropdown for forecast type
forecast_type = st.selectbox("Select Forecast Type", ["Short Term", "Long Term"])
 
# Load the historical data from the local file
historical_df = pd.read_csv(local_file_path)
 
# Prepare the data for prediction
def prepare_data_for_prediction(historical_data):
    # Assume the future dates and other necessary columns will be added by the model
    return historical_data
 
# Prepare combined data
combined_df = prepare_data_for_prediction(historical_df)
 
# Select the appropriate endpoint
if forecast_type == "Short Term":
    endpoint_name = SHORT_TERM_ENDPOINT_NAME
else:
    endpoint_name = LONG_TERM_ENDPOINT_NAME
 
# Display a button to trigger the forecast
if st.button("Get Forecast"):
    # Get the forecast
    forecast_df = get_forecast_from_sagemaker(combined_df, endpoint_name, AWS_REGION)
    if forecast_df is not None:
        if forecast_type == "Long Term":
            # Restrict long-term predictions to 365 days
            forecast_df = forecast_df.head(365)
        # Reset index to start from 1
        forecast_df.index = forecast_df.index + 1
        # Display the forecast
        st.subheader("Forecast")
        st.write("Stock prices are in INR.")
        st.write(forecast_df)
