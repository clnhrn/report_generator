## Setup

### Setting up the GCP Project

- Install the gcloud CLI: https://cloud.google.com/sdk/docs/install
- In the Google Cloud web console, create a new Google Cloud project (take note of the **project ID**) and enable the **Google Drive API**.
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

- Create a folder to store the **static** files (i.e. Employees sheet, Device Owner sheet). Take note of the file IDs.
- Create another folder to store the **output**. Take note of the folder ID.
  *You can get the ID from the file/folder URL.*

Please share folder access to the user running the program as needed.

## Installation

Install the required packages using pip

```bash
pip install -r requirements.txt
```

## Usage

Before running the script, make sure you are authenticated in the gcloud CLI and you are in the correct project.

```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
```

Now, you can run the program by providing the required parameters.

```bash
python main.py -p <Project-ID> -c <CrowdStrike-Secret-ID> -l <LastPass-Secret-ID> -e <Employees-Sheet-ID> -d <Device-Owner-Sheet-ID> -o <Output-Folder-ID>
``` 

Afterwards, an Excel file should be added to the output folder with the name **Report_YYYYMMDD**.

## Notes

When running the program for the first time, a browser window will automatically open, directing you to Google's login page. Login and proceed by clicking "Continue". Your credentials will be stored.