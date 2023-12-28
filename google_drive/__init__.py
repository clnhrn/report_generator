import os
import tempfile
from typing import Union, IO

import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


class GoogleDriveHelpers:
    def __init__(
        self,
        json_credentials_file: Union[str, os.PathLike] = None,
    ):
        self.json_credentials_file = json_credentials_file

    def create_drive_instance(self):
        gauth = GoogleAuth()
        gauth.settings["oauth_scope"] = ["https://www.googleapis.com/auth/drive"]

        gauth.LoadCredentialsFile(self.json_credentials_file)
        if gauth.credentials is None:
            # authenticate if there are no credentials
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            project_dir = os.path.abspath(os.getcwd())
            try: 
                # delete existing credentials file
                print(f'Delete existing credentials... {os.path.join(project_dir, "credentials.json")}')
                os.remove(os.path.join(project_dir, "credentials.json"))
            except FileNotFoundError:
                pass

            # load credentials again and authenticate
            gauth.LoadCredentialsFile(self.json_credentials_file)
            gauth.LocalWebserverAuth()
        else:
            # initialize the saved credentials
            gauth.Authorize()

        # save the current credentials to a file
        gauth.SaveCredentialsFile(self.json_credentials_file)

        self.drive = GoogleDrive(gauth)
        return self.drive

    def upload_file(
        self, content: IO, folder_id: str, filename: Union[str, os.PathLike]
    ):
        file = self.drive.CreateFile(
            {"title": filename, "parents": [{"id": folder_id}]}
        )
        file.SetContentFile(content.name)
        file.Upload()

    def download_file(self, file_id: str):
        file = self.drive.CreateFile({"id": file_id})
        temp_file = tempfile.NamedTemporaryFile()
        try:
            # download the content of the drive file and write it to the temporary file
            file.GetContentFile(temp_file.name)
            print(f"File downloaded: {temp_file.name}")
            df = pd.read_excel(temp_file)
            temp_file.close()
        except Exception as e:
            raise

        return df
