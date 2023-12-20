import os
import requests
import json
from typing import Union, Any

import pandas as pd
from google.cloud import secretmanager


class LastPassHelpers:
    base_url = "https://lastpass.com/enterpriseapi.php"

    def __init__(
        self,
        project_id: str = None,
        secret_id: str = None,
        json_credential_file: Union[str, os.PathLike] = None,
    ):
        self.project_id = project_id
        self.secret_id = secret_id
        self.json_credential_file = json_credential_file

    def get_credentials(self):
        if self.json_credential_file:
            with open(self.json_credential_file, "r") as file:
                secret_dict = json.load(file)
                cid = secret_dict["cid"]
                prov_hash = secret_dict["prov_hash"]

        else:
            client = secretmanager.SecretManagerServiceClient()
            r = client.access_secret_version(
                name=f"projects/{self.project_id}/secrets/{self.secret_id}/versions/latest"
            )

            data = r.payload.data
            data_str = data.decode()
            secret_dict = json.loads(data_str)

            cid = secret_dict["cid"]
            prov_hash = secret_dict["prov_hash"]

        return cid, prov_hash

    def save_response(
        self, response: dict[str, Any], filepath: Union[str, os.PathLike]
    ):
        with open(filepath, "w") as file:
            json.dump(response, file, indent=4)
            print("Response data written to users.json")

    def send_post_request(
        self, payload: dict[str, Any], filepath: Union[str, os.PathLike] = None
    ):
        # set headers
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(
                self.base_url, data=json.dumps(payload), headers=headers
            )
            # check response status
            if response.status_code == 200:
                data = response.json()
                if filepath:
                    self.save_response(data, filepath)
            else:
                print("Error:", response.status_code, response.text)
        except Exception as e:
            print(e)

        return data

    def get_user_data(self, filepath: Union[str, os.PathLike] = None):
        cid, prov_hash = self.get_credentials()

        payload = {
            "cid": cid,
            "provhash": prov_hash,
            "cmd": "getuserdata",
        }

        data = self.send_post_request(payload, filepath)

        return data


def account_status_condition(row):
    # expired invitation, active, disabled, invited
    if row["disabled"] == True:
        return "Disabled"
    else:
        if row["neverloggedin"] == True:
            return "Invited"
        elif row["neverloggedin"] == False:
            return "Active"
        elif row["neverloggedin"] == None:
            return "Expired Invitation"
        else:
            return None


def create_lastpass_report(
    project_id=None,
    secret_id=None,
    json_credential_file: Union[str, os.PathLike] = None,
):
    lp = LastPassHelpers(
        project_id=project_id,
        secret_id=secret_id,
        json_credential_file=json_credential_file,
    )

    user_dict = lp.get_user_data()

    # get user data dictionaries and create dataframe
    data = user_dict["Users"]
    inner_dicts = list(data.values())
    df = pd.DataFrame(inner_dicts)

    # get users with expired invitation
    try:
        invited_users = user_dict["invited"]

        row_index = len(df["username"])
        for user in invited_users:
            df.loc[row_index, "username"] = user
            df.loc[row_index, "neverloggedin"] = None
            row_index += 1
    except Exception:
        pass

    # create account_status column and populate
    df["account_status"] = df.apply(account_status_condition, axis=1)

    return df
