## Setup

### Setting up the GCP Project

- Create a new Google Cloud project (take note of the **project ID**) and enable the **Google Drive API**.
- Click **Create Credentials**. Fill in all required information.
- For the **OAuth Client ID** section, you can specify the **Application type** as a Desktop App.
- You will then be instructed to download your credentials. After downloading the JSON file, rename it to **client_secrets.json**. Place it in the project directory.
- Click **Done**.
- Navigate to *APIs & Services* > *OAuth consent screen*.
- In the **Test users** section, add the email address of the user who will run the program.

### Storing credentials in Secret Manager

To run the program, you will need credentials from LastPass and CrowdStrike.

CrowdStrike_credentials.json 
```bash
{"client_id": "*****", "client_secret": "*****"}
```
LastPass_credentials.json
```bash
{"cid": "*****", "prov_hash": "*****"}
``` 
- Open the Google Cloud console and navigate to *Security* > *Secret Manager*.
- Enable the **Secret Manager API**.
- Click **Create Secret**.
- Provide a name (secret ID) to your secret. For example: LP_secret
- Upload the corresponding JSON file as the secret value.

You will need two secrets. One for Crowdstrike and another for LastPass. Take note of the secret name/ID.

### Google Drive Setup

- Create a folder to store the **static** files (i.e. Monday sheet, Device Owner sheet). Take note of the file IDs.
- Create another folder to store the **output**. Take note of the folder ID.
  *You can get the ID from the file/folder URL.*

Please share folder access to the user running the program as needed.

## Installation

Install the required packages using pip

```bash
pip install -r requirements.txt
```

## Usage

In your terminal, input the command below and press Enter.

```bash
python main.py <Project-ID> <CrowdStrike-Secret-ID> <LastPass-Secret-ID> 
<Monday-Sheet-ID> <Device-Owner-Sheet-ID> <Output-Folder-ID>
``` 

After running the program, an Excel file should be added to the output folder with the name **Report_YYYYMMDD**.

## Notes

When running the program for the first time, a browser window will automatically open, directing you to Google's login page. Login and proceed by clicking "Continue". 

Your credentials will be stored and future runs will no longer require you to log back in.