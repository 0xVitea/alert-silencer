import logging
from typing import Any, Dict, List

from robusta.api import (ActionParams, CallbackBlock, CallbackChoice,
                         ExecutionBaseEvent, PrometheusKubernetesAlert, action)


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
def silencer(event: ExecutionBaseEvent, params: AlertManagerParams):
    logging.info(params.alert_labels)
    logging.info(params.alert_manager_url)
    logging.info(params.silence_interval)
    print(100 * "*")


# silence_enricher - main silence enrichment function
@action
def silence_enricher(alert: PrometheusKubernetesAlert, params: AlertManagerURL):
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
