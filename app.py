import streamlit as st
import boto3
import pandas as pd
import io
import altair as alt

# Load AWS credentials from Streamlit secrets
aws_access_key_id = st.secrets["aws_access_key_id"]
aws_secret_access_key = st.secrets["aws_secret_access_key"]
aws_region = st.secrets["region"]

# Define the SageMaker endpoint names
SHORT_TERM_ENDPOINT_NAME = "canvas-shortterm"
LONG_TERM_ENDPOINT_NAME = "canvas-new-deployment-07-11-2024-2-00-AM"

# Local path where the downloaded file is saved
local_file_path = 'newprocessed_TATAMOTORS.NS_stock_data.csv'

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

# Function to filter out weekends from the forecast data
def filter_weekends(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df = df[df['Date'].dt.dayofweek < 5]  # Keep only weekdays (0 = Monday, ..., 4 = Friday)
    return df

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
    forecast_df = get_forecast_from_sagemaker(combined_df, endpoint_name, aws_region, aws_access_key_id, aws_secret_access_key)
    if forecast_df is not None:
        # Filter out weekends
        forecast_df = filter_weekends(forecast_df)
        
        # Reset index to start from 1
        forecast_df.index = forecast_df.index + 1
        
        # Display the next day's prediction
        st.subheader("Prediction for the Next Day")
        next_day_forecast = forecast_df.head(1)
        st.write(next_day_forecast[["Date", "mean", "p10", "p50", "p90"]])
        
        # Display the full forecast table with probabilities
        st.subheader("Full Forecast with Probabilities")
        st.write(forecast_df[["Date", "mean", "p10", "p50", "p90"]])
        
        # Create and display a line chart for the forecast with error bands
        base = alt.Chart(forecast_df).encode(x='Date:T')

        line = base.mark_line().encode(
            y='mean:Q',
            color=alt.value('blue'),
            tooltip=['Date:T', 'mean:Q']
        )

        band = base.mark_area(opacity=0.3).encode(
            y='p10:Q',
            y2='p90:Q'
        )

        chart_with_band = band + line
        st.altair_chart(chart_with_band, use_container_width=True)

        # Combined historical and forecast chart for meaningful analysis
        combined_chart = alt.Chart(pd.concat([historical_df, forecast_df])).mark_line().encode(
            x='Date:T',
            y=alt.Y('mean:Q', title='Price (INR)'),
            tooltip=['Date:T', 'mean:Q', 'p10:Q', 'p50:Q', 'p90:Q']
        ).properties(
            width=800,
            height=400
        ).interactive()

        st.altair_chart(combined_chart, use_container_width=True)

        # Probability distribution chart for the forecast
        st.subheader("Probability Distribution of Forecasted Prices")
        probability_chart = alt.Chart(forecast_df).transform_density(
            'mean',
            as_=['mean', 'density'],
        ).mark_area().encode(
            x='mean:Q',
            y='density:Q'
        ).properties(
            width=800,
            height=400
        )

        st.altair_chart(probability_chart, use_container_width=True)
