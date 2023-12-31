import os
import argparse
import tempfile
from datetime import datetime
from typing import Union
import warnings
import pandas as pd

from google_drive import GoogleDriveHelpers
from lastpass import create_lastpass_report
from crowdstrike import create_crowdstrike_report
from helpers import select_columns_by_name


warnings.filterwarnings(action="ignore", category=pd.errors.SettingWithCopyWarning)


def generate_report(
    project_id: str,
    cs_secret_id: str,
    lp_secret_id: str,
    employees_file_id: str,
    device_owner_file_id: str,
    target_drive_folder_id: str,
    cs_json_credential_file: Union[str, os.PathLike] = None,
    lp_json_credential_file: Union[str, os.PathLike] = None,
    drive_json_credential_file: Union[str, os.PathLike] = "credentials.json",
):
    drive_obj = GoogleDriveHelpers(drive_json_credential_file)
    drive_obj.create_drive_instance()

    employees_data = drive_obj.download_file(employees_file_id)
    device_owner_data = drive_obj.download_file(device_owner_file_id)

    cs_data = create_crowdstrike_report(
        project_id, cs_secret_id, cs_json_credential_file
    )
    lp_data = create_lastpass_report(project_id, lp_secret_id, lp_json_credential_file)

    # get the columns: First Name, Last Name, SynMax Email
    main_sheet = select_columns_by_name(
        employees_data, ["First Name", "Last Name", "SynMax Email"]
    )
    main_sheet.dropna(subset=["First Name"], inplace=True)
    main_sheet.dropna(subset=["Last Name"], inplace=True)

    main_sheet.loc[:, "First Name"] = main_sheet["First Name"].str.strip()
    main_sheet.loc[:, "Last Name"] = main_sheet["Last Name"].str.strip()
    # remove the parentheses and the characters in it
    main_sheet.loc[:, "Last Name"] = main_sheet["Last Name"].str.replace(r'\s*\([^)]*\)', '', regex=True)
    main_sheet.loc[:, "SynMax Email"] = main_sheet["SynMax Email"].str.strip()
    main_sheet.loc[:, "SynMax Email"] = main_sheet["SynMax Email"].str.lower()


    # get the columns: Host Name, First Name, Last Name
    device_sheet = select_columns_by_name(
        device_owner_data, ["Host Name", "First Name", "Last Name"]
    )
    device_sheet.loc[:, "First Name"] = device_sheet["First Name"].str.strip()
    device_sheet.loc[:, "Last Name"] = device_sheet["Last Name"].str.strip()
    device_sheet.loc[:, "Host Name"] = device_sheet["Host Name"].str.strip()

    # get the columns: hostname, last_seen_utc
    cs_sheet = select_columns_by_name(
        cs_data, ["hostname", "last_seen_utc", "first_seen_utc", "stale_period (days)"]
    )
    cs_sheet.loc[:, "hostname"] = cs_sheet["hostname"].str.strip()

    # get the columns: username, account_status, last_login
    lp_sheet = select_columns_by_name(
        lp_data, ["username", "account_status", "last_login"]
    )
    lp_sheet.loc[:, "username"] = lp_sheet["username"].str.strip()

    # MATCH CS TO DEVICE OWNER USING HOST NAME
    device_sheet.loc[:, "device_host_lower"] = device_sheet["Host Name"].str.lower()
    cs_sheet.loc[:, "cs_host_lower"] = cs_sheet["hostname"].str.lower()
    df_merged = cs_sheet.merge(
        device_sheet, left_on="cs_host_lower", right_on="device_host_lower", how="left"
    )
    host_df = df_merged[
        [
            "hostname",
            "First Name",
            "Last Name",
            "last_seen_utc",
            "first_seen_utc",
            "stale_period (days)",
        ]
    ]
    host_df.rename(
        columns={
            "hostname": "Host Name",
            "last_seen_utc": "CrowdStrike Last Seen (UTC)",
            "first_seen_utc": "CrowdStrike First Seen (UTC)",
            "stale_period (days)": "CrowdStrike Stale Period (days)",
        },
        inplace=True,
    )

    # MATCH DEVICE OWNER TO EMPLOYEE NAMES
    main_sheet.loc[:, "first_name_lower"] = main_sheet["First Name"].str.lower()
    main_sheet.loc[:, "last_name_lower"] = main_sheet["Last Name"].str.lower()
    host_df.loc[:, "first_name_lower_host"] = host_df["First Name"].str.lower()
    host_df.loc[:, "last_name_lower_host"] = host_df["Last Name"].str.lower()
    df_merged = main_sheet.merge(
        host_df,
        left_on=["first_name_lower", "last_name_lower"],
        right_on=["first_name_lower_host", "last_name_lower_host"],
        how="outer",
    )
    main_host_df = df_merged[
        [
            "First Name_x",
            "Last Name_x",
            "SynMax Email",
            "Host Name",
            "CrowdStrike Last Seen (UTC)",
            "CrowdStrike First Seen (UTC)",
            "CrowdStrike Stale Period (days)",
        ]
    ]
    host_df.drop(["first_name_lower_host"], axis=1, inplace=True)
    host_df.drop(["last_name_lower_host"], axis=1, inplace=True)

    # MATCH EMAILS
    df_merged = main_host_df.merge(
        lp_sheet, left_on="SynMax Email", right_on="username", how="left"
    )
    final_df = df_merged[
        [
            "Last Name_x",
            "First Name_x",
            "SynMax Email",
            "Host Name",
            "CrowdStrike Last Seen (UTC)",
            "CrowdStrike First Seen (UTC)",
            "CrowdStrike Stale Period (days)",
            "account_status",
            "last_login",
        ]
    ]
    final_df.rename(
        columns={
            "account_status": "LastPass Account Status",
            "last_login": "LastPass Last Login",
            "First Name_x": "First Name",
            "Last Name_x": "Last Name",
        },
        inplace=True,
    )

    final_df.drop_duplicates(subset=['Host Name'], keep="first", inplace=True)

    # save df in tempfile
    excel_buffer = tempfile.NamedTemporaryFile()
    final_df.to_excel(excel_buffer, sheet_name="main", engine="openpyxl", index=False)
    excel_buffer.seek(0)

    # get the current date
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y%m%d")

    # upload to drive
    drive_obj.upload_file(
        excel_buffer,
        target_drive_folder_id,
        f"Report_{formatted_date}.xlsx",
    )

    print("Report uploaded to Google Drive.")


def main():
    parser = argparse.ArgumentParser(
        description="Program to generate and upload a report to Google Drive directly."
    )
    parser.add_argument("-p", "--project_id", help="Project ID from the Google Cloud console")
    parser.add_argument("-c", "--cs_id", help="Secret ID of the CrowdStrike credentials")
    parser.add_argument("-l", "--lp_id", help="Secret ID of the LastPass credentials")
    parser.add_argument("-e", "--employees_id", help="File ID of the Monday sheet")
    parser.add_argument("-d", "--device_owner_id", help="File ID of the Device Owner sheet")
    parser.add_argument("-o", "--output_id", help="Folder ID of the output folder")

    args = parser.parse_args()

    generate_report(
        project_id=args.project_id,
        cs_secret_id=args.cs_id,
        lp_secret_id=args.lp_id,
        employees_file_id=args.employees_id,
        device_owner_file_id=args.device_owner_id,
        target_drive_folder_id=args.output_id,
    )


# RUN THE PROGRAM BY PROVIDING THE REQUIRED PARAMETERS IN THE TERMINAL
if __name__ == "__main__":
    main()


# RUN THE PROGRAM USING "python main.py"
# if __name__ == "__main__":
#     # from GCP
#     project_id = ""
#     cs_secret_id = ""
#     lp_secret_id = ""

#     # static file ids
#     monday_file_id = ""
#     device_owner_file_id = ""

#     # output folder id
#     drive_folder_id = ""

#     generate_report(
#         project_id=project_id,
#         cs_secret_id=cs_secret_id,
#         lp_secret_id=lp_secret_id,
#         target_drive_folder_id=drive_folder_id,
#         monday_file_id=monday_file_id,
#         device_owner_file_id=device_owner_file_id,
#     )
