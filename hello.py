import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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
    print(worksheet.title)
    records = worksheet.get_all_records()

    # Convert records to a DataFrame
    df = pd.DataFrame(records)

    # I only care about these fields
    df = df[['Date', 'Distance', 'Time', 'Average HR']]

    # Remove rows where 'Distance' is an empty string
    df = df[df['Distance'].astype(bool)]

    # Ensure the date column is in datetime format
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')

    # Append the data to the all_data DataFrame
    all_data = all_data._append(df, ignore_index=True)

# Sort the data by date
all_data.sort_values('Date', inplace=True)


# Convert 'Distance' to float for calculations
all_data['Distance'] = all_data['Distance'].astype(float)

# Calculate the moving average
window_size = 30  # You can adjust this window size for more or less smoothing
all_data['Smoothed Distance'] = all_data['Distance'].rolling(window=window_size, min_periods=1).mean()

# Plot the data in XKCD style
with plt.xkcd():
    plt.figure(figsize=(10, 6))
    plt.plot(all_data['Date'], all_data['Smoothed Distance'], marker='o', label='Smoothed Distance')
    plt.title('Overall Distance Run (Smoothed)')
    plt.xlabel('Date')
    plt.ylabel('Distance')
    plt.grid(True)
    plt.legend()
    plt.show()