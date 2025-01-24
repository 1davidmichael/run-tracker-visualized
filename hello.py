from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.graph_objects as go
import numpy as np

app = FastAPI()

def generate_plots():
    # Set up the Google Sheets API client using a service account
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/david.michael/.config/gspread/service_account.json', scope)
    client = gspread.authorize(creds)

    # Open the Google Sheet
    spreadsheet = client.open('Running Log')

    # Initialize an empty DataFrame to store all data
    all_data = pd.DataFrame()

    # Iterate over each worksheet (tab) in the spreadsheet
    for worksheet in spreadsheet.worksheets():
        # Get all records from the current worksheet
        records = worksheet.get_all_records()

        # Convert records to a DataFrame
        df = pd.DataFrame(records)

        # I only care about these fields
        df = df[['Date', 'Distance', 'Time', 'Average HR']]

        # Remove rows where 'Distance' is an empty string
        df = df[df['Distance'].astype(bool)]

        # Ensure the date column is in datetime format
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')

        # Convert 'Time' to timedelta
        df['Time'] = pd.to_timedelta(df['Time'])

        # Append the data to the all_data DataFrame
        all_data = all_data._append(df, ignore_index=True)

    # Sort the data by date
    all_data.sort_values('Date', inplace=True)

    # Convert 'Distance' to float for calculations
    all_data['Distance'] = all_data['Distance'].astype(float)
    all_data['Average HR'] = all_data['Average HR'].astype(float)

    # Calculate pace (minutes per mile)
    all_data['Pace'] = (all_data['Time'].dt.total_seconds() / 60) / all_data['Distance']

    # Add a trend line
    # Convert dates to ordinal numbers for regression
    dates_ordinal = all_data['Date'].map(pd.Timestamp.toordinal)
    # Perform linear regression
    slope, intercept = np.polyfit(dates_ordinal, all_data['Pace'], 1)
    # Calculate trend line values
    trend_line = slope * dates_ordinal + intercept

    # Create a Plotly figure for Pace
    fig_pace = go.Figure()

    # Add scatter plot for Pace
    fig_pace.add_trace(go.Scatter(x=all_data['Date'], y=all_data['Pace'], mode='markers', name='Pace (min/mile)', marker=dict(color='blue')))

    # Add line for Trend Line
    fig_pace.add_trace(go.Scatter(x=all_data['Date'], y=trend_line, mode='lines', name='Trend Line', line=dict(color='green')))

    # Update layout for Pace plot
    fig_pace.update_layout(title='Average Pace Over Time with Trend Line',
                           xaxis_title='Date',
                           yaxis_title='Pace (min/mile)')

    # Create a Plotly figure for Average HR
    fig_hr = go.Figure()

    # Add scatter plot for Average HR
    fig_hr.add_trace(go.Scatter(x=all_data['Date'], y=all_data['Average HR'], mode='markers', name='Average HR', marker=dict(color='purple')))

    # Update layout for HR plot
    fig_hr.update_layout(title='Average Heart Rate Over Time',
                         xaxis_title='Date',
                         yaxis_title='Average HR')

    # Create a Plotly figure for Total Distance
    fig_distance = go.Figure()

    # Add line plot for Total Distance
    fig_distance.add_trace(go.Scatter(x=all_data['Date'], y=all_data['Distance'].cumsum(), mode='lines', name='Total Distance', line=dict(color='orange')))

    # Update layout for Distance plot
    fig_distance.update_layout(title='Total Distance Over Time',
                               xaxis_title='Date',
                               yaxis_title='Total Distance (miles)')

    # Create a 3D Plotly figure for Pace vs. HR over Time
    fig_pace_hr_time_3d = go.Figure()

    # Add 3D scatter plot for Pace vs. HR over Time
    fig_pace_hr_time_3d.add_trace(go.Scatter3d(
        x=all_data['Pace'],
        y=all_data['Average HR'],
        z=dates_ordinal,  # Use ordinal dates for z-axis
        mode='markers',
        marker=dict(size=5, color=dates_ordinal, colorscale='Viridis', opacity=0.8),
        name='Pace vs. HR over Time'
    ))

    # Convert a few ordinal dates back to strings for tick labels
    tickvals = dates_ordinal[::max(1, len(dates_ordinal)//10)]  # Select a few dates for ticks
    ticktext = [pd.Timestamp.fromordinal(int(date)).strftime('%Y-%m-%d') for date in tickvals]

    # Update layout for 3D plot
    fig_pace_hr_time_3d.update_layout(title='3D Plot of Pace vs. Heart Rate Over Time',
                                      scene=dict(
                                          xaxis_title='Pace (min/mile)',
                                          yaxis_title='Average HR',
                                          zaxis=dict(title='Date', tickvals=tickvals, ticktext=ticktext)
                                      ))

    # Return the HTML representation of the plots
    return (fig_pace.to_html(full_html=False),
            fig_hr.to_html(full_html=False),
            fig_distance.to_html(full_html=False),
            fig_pace_hr_time_3d.to_html(full_html=False))

@app.get("/", response_class=HTMLResponse)
async def root():
    plot_pace_html, plot_hr_html, plot_distance_html, plot_pace_hr_time_3d_html = generate_plots()
    return f"<html><body>{plot_pace_html}<br><br>{plot_hr_html}<br><br>{plot_distance_html}<br><br>{plot_pace_hr_time_3d_html}</body></html>"
