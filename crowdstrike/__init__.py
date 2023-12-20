import os
import json
from datetime import datetime, timezone
from dateutil import parser as dparser
from typing import Union

import pandas as pd
from falconpy import Hosts
from google.cloud import secretmanager


class CSFalconHelpers:
    def __init__(
        self,
        project_id: str = None,
        secret_id: str = None,
        json_credential_file: Union[str, os.PathLike] = None,
    ):
        self.project_id = project_id
        self.secret_id = secret_id
        self.json_credential_file = json_credential_file

        client_id, client_secret = self.get_credentials()
        self.falcon = Hosts(client_id=client_id, client_secret=client_secret)

    def get_credentials(self):
        if self.json_credential_file:
            with open(self.json_credential_file, "r") as file:
                secret_dict = json.load(file)
                client_id = secret_dict["client_id"]
                client_secret = secret_dict["client_secret"]

        else:
            client = secretmanager.SecretManagerServiceClient()
            response = client.access_secret_version(
                name=f"projects/{self.project_id}/secrets/{self.secret_id}/versions/latest"
            )
            data = response.payload.data
            data_str = data.decode()
            secret_dict = json.loads(data_str)

            client_id = secret_dict["client_id"]
            client_secret = secret_dict["client_secret"]

        return client_id, client_secret

    def device_list(self, off: int, limit: int, sort: str) -> tuple:
        try:
            result = self.falcon.query_devices_by_filter(
                limit=limit, offset=off, sort=sort
            )
        except Exception:
            raise

        new_offset = result["body"]["meta"]["pagination"]["offset"]
        total = result["body"]["meta"]["pagination"]["total"]
        returned_device_list = result["body"]["resources"]

        return new_offset, total, returned_device_list

    def device_detail(self, agent_ids: list) -> list:
        try:
            result = self.falcon.get_device_details(ids=agent_ids)
        except Exception:
            raise
        device_details = []

        now = datetime.now(timezone.utc)
        
        # return hostname and last_seen
        for device in result["body"]["resources"]:
            res = {}
            then = dparser.parse(device.get("last_seen"), None)
            distance = (now - then).days
            res["hostname"] = device.get("hostname", None)
            res["last_seen"] = device.get("last_seen", None)
            res["first_seen"] = device.get("first_seen", None)
            res["stale_period (days)"] = f"{distance}"
            device_details.append(res)

        return device_details


def convert_date_format(date_str):
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    else:
        return None


def create_crowdstrike_report(
    project_id: str = None,
    secret_id: str = None,
    json_credential_file: Union[str, os.PathLike] = None,
) -> pd.DataFrame:
    sort = "hostname.asc"
    offset = 0
    displayed = 0
    total = 1
    limit = 500

    devices_lst = []

    falcon_helper = CSFalconHelpers(
        project_id=project_id,
        secret_id=secret_id,
        json_credential_file=json_credential_file,
    )

    while offset < total:
        offset, total, devices = falcon_helper.device_list(offset, limit, sort)
        details = falcon_helper.device_detail(devices)
        for detail in details:
            displayed += 1
            print(
                f"{displayed}: {detail['hostname']} was last seen on {detail['last_seen']}"
            )
            devices_lst.append(detail)

    df = pd.DataFrame(devices_lst)
    
    # convert date format
    df["last_seen_utc"] = df["last_seen"].apply(lambda x: convert_date_format(x))
    df["first_seen_utc"] = df["first_seen"].apply(lambda x: convert_date_format(x))
    return df
