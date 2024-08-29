# Job Application Tracker

## Description

The Job Application Tracker is a PyQt6-based desktop application designed to help job seekers manage and track their job applications efficiently. This comprehensive tool allows users to input, store, and visualize data related to their job search process.

## Features

1. **Data Entry**: Users can input detailed information about each job application, including:

   - Company name
   - Job title
   - Job position
   - Application status
   - Company website
   - Location
   - Salary range
   - Application method
   - Resume version
   - Cover letter version
   - Application date
   - Interview date
   - Follow-up date
   - And more...

2. **Data Management**:

   - View all entries in a sortable table
   - Edit existing entries
   - Delete entries

3. **File Management**:

   - Upload and manage different versions of resumes and cover letters
   - Data is automatically saved in a local file (job_applications.pkl)

4. **Data Visualization**: The application provides a comprehensive dashboard with various charts and graphs, including:

   - Applications by status (pie chart)
   - Top companies by applications (bar chart)
   - Applications over time (line chart)
   - Top 10 job positions (bar chart)
   - Applications by term (bar chart)
   - Applications by method (bar chart)
   - Applications by resume and cover letter version (bar charts)
   - Application statuses over time (stacked area chart)
   - Applications by industry (pie chart)

5. **Data Import/Export**:
   - Import data from Excel (.xlsx) or CSV files
   - Export data to Excel or CSV formats

## Requirements

- Python 3.x
- PyQt6
- pandas
- matplotlib
- numpy

## Installation

1. Ensure you have Python 3.x installed on your system.
2. Install the required libraries using pip:

   ```
   pip install -r requirements.txt
   ```

## How to Run

1. Save the provided Python script as `job_tracker_pyqt.py`.
2. Open a terminal or command prompt.
3. Navigate to the directory containing the script.
4. Run the following command:

   ```
   python job_tracker_pyqt.py
   ```

5. The Job Application Tracker window should appear, ready for use.

## Usage

1. **Adding a New Entry**:

   - Fill in the required fields (marked with \*) and any additional information.
   - Click the "Add Entry" button.

2. **Viewing Entries**:

   - Click the "View Entries" button to see all your job applications in a table format.
   - Use the search bar to filter entries.

3. **Editing an Entry**:

   - In the "View Entries" window, select an entry and click the "Edit" button.
   - Modify the information in the pop-up window and click "Save".

4. **Deleting an Entry**:

   - In the "View Entries" window, select an entry and click the "Delete" button.
   - Confirm the deletion when prompted.

5. **Uploading Resume/Cover Letter**:

   - When adding or editing an entry, click the "Upload Resume" or "Upload Cover Letter" button.
   - Select the file from your computer.

6. **Viewing Dashboard**:

   - Click on the "Dashboard" tab to view various charts and statistics about your job applications.

7. **Exporting Data**:

   - Click the "Save As" button to export your data to Excel or CSV format.

8. **Importing Data**:
   - Click the "Import File" button to import data from an Excel or CSV file.
   - Map the columns from your file to the application's fields.

## Notes

- The application automatically saves your data after each action.
- Uploaded resumes and cover letters are stored in the `resume` and `cover_letter` folders within the application directory.
- The dashboard updates automatically when you add, edit, or delete entries.

## Troubleshooting

If you encounter any issues:

- Check the `app.log` file in the application directory for error messages.
- Ensure all required libraries are installed and up to date.
- Verify that you have write permissions in the application directory.

## Future Improvements

- Implement user authentication for multi-user support.
- Add email reminders for follow-ups and interviews.
- Integrate with job search APIs for automatic job listing imports.
- Develop a mobile companion app for on-the-go updates.
