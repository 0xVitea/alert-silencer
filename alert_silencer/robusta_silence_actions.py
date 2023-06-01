import logging

from robusta.api import (ActionParams, CallbackBlock, CallbackChoice,
                         ExecutionBaseEvent, PrometheusKubernetesAlert, action)


class AlertManagerURL(ActionParams):
    """
    :var alert_manager_url: Alert Manager url
    """
    alert_manager_url: str


class AlertManagerParams(AlertManagerURL):
    """
    :var alert_label: Alert Name
    """
    alert_label: str


@action
def sampler(event: ExecutionBaseEvent, params: AlertManagerParams):
    logging.info(params.alert_label)
    logging.info(params.alert_manager_url)


@action
def silence_enricher(alert: PrometheusKubernetesAlert, params: AlertManagerURL):
    """
    Add a button to the alert - clicking it to silence the alert
    """
    alert.add_enrichment(
        [
            CallbackBlock(
                {
                    "Silence for 15 minutes": CallbackChoice(
                        action=sampler,
                        action_params=AlertManagerParams(
                            alert_label=alert.alert.labels.get("alertname", ""),
                            alert_manager_url=params.alert_manager_url,
                        ),
                    )
                },
            )
        ]
    )
