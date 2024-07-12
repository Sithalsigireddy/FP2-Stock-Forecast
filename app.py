import streamlit as st
import boto3
import pandas as pd
import io

# Load AWS credentials from Streamlit secrets
aws_access_key_id = st.secrets["aws_access_key_id"]
aws_secret_access_key = st.secrets["aws_secret_access_key"]
aws_region = st.secrets["region"]

# Define the SageMaker endpoint names
SHORT_TERM_ENDPOINT_NAME = "canvas-shortterm"  # Short-term endpoint name
LONG_TERM_ENDPOINT_NAME = "canvas-new-deployment-07-11-2024-2-00-AM"  # Long-term endpoint name

# Local paths for the CSV files
short_term_file_path = 'deploy.csv'
long_term_file_path = 'newprocessed_TATAMOTORS.NS_stock_data.csv'

# Function to call the SageMaker endpoint
def get_forecast_from_sagemaker(data, endpoint_name, aws_region, aws_access_key_id, aws_secret_access_key):
    client = boto3.client(
        "runtime.sagemaker", 
        region_name=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
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

# Load the appropriate historical data based on the forecast type
if forecast_type == "Short Term":
    historical_df = pd.read_csv(short_term_file_path)
    endpoint_name = SHORT_TERM_ENDPOINT_NAME
else:
    historical_df = pd.read_csv(long_term_file_path)
    endpoint_name = LONG_TERM_ENDPOINT_NAME

# Prepare the data for prediction
def prepare_data_for_prediction(historical_data):
    # Assume the future dates and other necessary columns will be added by the model
    return historical_data

# Prepare combined data
combined_df = prepare_data_for_prediction(historical_df)

# Display a button to trigger the forecast
if st.button("Get Forecast"):
    # Get the forecast
    forecast_df = get_forecast_from_sagemaker(combined_df, endpoint_name, aws_region, aws_access_key_id, aws_secret_access_key)
    if forecast_df is not None:
        if forecast_type == "Long Term":
            # Restrict long-term predictions to 365 days
            forecast_df = forecast_df.head(365)
        
        # Convert 'Date' column to datetime
        forecast_df['Date'] = pd.to_datetime(forecast_df['Date']).dt.date
        
        # Create a mask for weekends
        is_weekend = forecast_df['Date'].dt.dayofweek.isin([5, 6])
        
        # Replace values for weekends with the message
        forecast_df.loc[is_weekend, ['mean', 'p10', 'p50', 'p90']] = "Weekend - Market is closed"
        
        # Reset index to start from 1
        forecast_df.index = forecast_df.index + 1
        
        # Display the forecast
        st.subheader("Forecast")
        st.write("Stock prices are in INR.")
        
        # Separate the mean forecast from the probabilities
        forecast_mean_df = forecast_df[['Date', 'mean']].copy()
        forecast_probabilities_df = forecast_df[['Date', 'p10', 'p50', 'p90']].copy()
        
        # Display the forecasted values
        st.write("### Forecasted Values")
        st.table(forecast_mean_df)
        
        # Display the probabilities
        st.write("### Probabilities")
        st.table(forecast_probabilities_df)
        
        # Display a note about market closure on weekends
        st.write("*Note: The market is closed on Saturdays and Sundays.*")
