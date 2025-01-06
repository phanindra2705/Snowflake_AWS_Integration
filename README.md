# Export-Import Management System

This project is a web application for managing data export and import processes with cloud storage integration. The application allows users to export data from Snowflake to AWS S3, import data from AWS S3 to Snowflake, and receive email notifications for successful operations.

## Features

- **User Management**:
  - Signup and Signin functionality with secure password storage using hashing.
  - Session management to ensure secure and authenticated access.

- **Data Export**:
  - Fetch data from Snowflake.
  - Export data as CSV files and upload them to an AWS S3 bucket.
  - Receive email notifications on successful export.

- **Data Import**:
  - Fetch CSV files from an AWS S3 bucket.
  - Import data into Snowflake tables.
  - Receive email notifications on successful import.

- **Email Notifications**:
  - Automated email notifications for both export and import operations.
  - Configurable email sender using Flask-Mail.

- **Cloud Integration**:
  - AWS S3 for file storage.
  - Snowflake for database management.

## Technologies Used

- **Backend**: Python, Flask, Flask-Mail
- **Frontend**: HTML, CSS, JavaScript
- **Database**: Snowflake
- **Cloud Storage**: AWS S3
- **Others**: Pandas, Boto3, Flask-Session

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.x
- Pip (Python package manager)
- AWS CLI configured with appropriate permissions
- Snowflake account and credentials




