import logging
import time
from dataclasses import dataclass
from datetime import datetime
from re import findall
from typing import Any, Dict, List, Optional

import requests


# Extract int from a string
def extract_int(arg: str) -> int:
    val = findall(r"\d+", arg)

    if len(val) == 0:
        raise Exception("String doesn't contain integers")

    return int(val[0])


@dataclass
class SilenceRuleResponse:
    created_new_rule: bool


class AlertManagerSilence:
    def __init__(self, alert_manager_url: str) -> None:
        self.alert_manager_url: str = alert_manager_url
        self.loaded_silence_rules: Optional[List[Dict[Any, Any]]] = None

    # Load silence rules from prometheus manager
    def load_silence_rules(self) -> None:
        # Sent a get request
        response = requests.get(f"{self.alert_manager_url}/api/v2/silences")
        response.raise_for_status()

        silence_rules = response.json()

        # Filter only active silence rules
        active_silence_rules: Optional[List[Dict[Any, Any]]] = []
        for silence_rule in silence_rules or []:
            if silence_rule["status"]["state"] == "active":
                active_silence_rules.append(silence_rule)

        logging.debug(f"Loaded alertmanager {self.alert_manager_url} rules")
        logging.debug(f"Loaded rules: {active_silence_rules}")
        self.loaded_silence_rules = active_silence_rules

    # Deletes a silence rule matched by id
    def delete_silence_rule(self, silence_rule_id: str) -> None:
        # Send a delete request
        response = requests.delete(
            f"{self.alert_manager_url}/api/v2/silence/{silence_rule_id}"
        )
        response.raise_for_status()

        logging.debug(f"Deleted silence rule id: {silence_rule_id}")

    # Creates silence rule in the alert manager
    def silence_rule(
        self, alert_labels: Dict[Any, Any], hour_interval: int
    ) -> Optional[SilenceRuleResponse]:
        # Format alert labels
        label_matchers: Optional[List[Dict[Any, Any]]] = []
        for i, (k, v) in enumerate(alert_labels.items()):
            label_matchers.append(
                {"name": k, "value": v, "isRegex": False, "isEqual": True}
            )

        # Check if the silence rule exists
        existing_silence_rule = self._check_existing_silence_rule(label_matchers)
        if existing_silence_rule is not None:
            # If the silence period is not gradual simply log
            if hour_interval <= extract_int(existing_silence_rule["comment"]):
                logging.info(f"This silence already exists: {existing_silence_rule}")
                return SilenceRuleResponse(False)

            # If the silence in gradual delete the existing silence rule and create the new one
            self.delete_silence_rule(existing_silence_rule["id"])

        # Post a silence rule
        response = requests.post(
            f"{self.alert_manager_url}/api/v2/silences",
            json={
                "matchers": label_matchers,
                "startsAt": datetime.utcfromtimestamp(time.time()).isoformat(),
                "endsAt": datetime.utcfromtimestamp(
                    time.time() + hour_interval * 3600
                ).isoformat(),
                "createdBy": "robusta-silencer",
                "comment": f"{hour_interval}h",
            },
        )
        response.raise_for_status()

        logging.info(f"Successfully silenced for {hour_interval} hours :{alert_labels}")

        return SilenceRuleResponse(True)

    # Checks if the silence rules with the same labels exists
    # Returns the existent silence rule
    def _check_existing_silence_rule(
        self, alert_labels: List[Dict[Any, Any]]
    ) -> Optional[Dict[Any, Any]]:
        for silence_rule in self.loaded_silence_rules or []:
            if (
                silence_rule["matchers"] == alert_labels
                and silence_rule["createdBy"] == "robusta-silencer"
            ):
                return silence_rule

        return None
