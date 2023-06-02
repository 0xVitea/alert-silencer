import logging
from typing import Any, Dict, List

from robusta.api import (ActionParams, CallbackBlock, CallbackChoice,
                         ExecutionBaseEvent, PrometheusKubernetesAlert, action)

from alertmanager import AlertManagerSilence


class AlertManagerURL(ActionParams):
    """
    :var alert_manager_url: Alert Manager url
    """

    alert_manager_url: str


class AlertManagerParams(AlertManagerURL):
    """
    :var alert_labels: Alert Name
    :var silence_interval: Interval for silencing in hours
    """

    alert_labels: Dict[Any, Any]
    silence_interval: int


# silencer - enricher callback function
@action
def silencer(event: ExecutionBaseEvent, params: AlertManagerParams) -> None:
    # Initiate alert silencer
    alert_silencer = AlertManagerSilence(alert_manager_url=params.alert_manager_url)
    silence_response = alert_silencer.silence_rule(
        alert_labels=params.alert_labels, hour_interval=params.silence_interval
    )


# silence_enricher - main silence enrichment function
@action
def silence_enricher(alert: PrometheusKubernetesAlert, params: AlertManagerURL) -> None:
    """
    Add a button to the alert - clicking it to silence the alert
    """

    # List of silence intervals in hours
    silence_intervals_hours: List[int] = [1, 4, 24]

    for interval in silence_intervals_hours:
        alert.add_enrichment(
            [
                CallbackBlock(
                    {
                        f"Silence for {interval}h": CallbackChoice(
                            action=silencer,
                            action_params=AlertManagerParams(
                                alert_labels=alert.alert.labels,
                                alert_manager_url=params.alert_manager_url,
                                silence_interval=interval,
                            ),
                        )
                    },
                )
            ]
        )
