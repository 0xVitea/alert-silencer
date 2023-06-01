import logging

from robusta.api import action, PrometheusKubernetesAlert, ActionParams, \
    CallbackBlock, CallbackChoice, ExecutionBaseEvent


class AlertManagerURL(ActionParams):
    """
    :var alert_manager_url: Alert Manager url
    """
    alert_manager_url: str


class AlertManagerParams(AlertManagerURL):
    """
    :var alert_name: Alert Name
    """
    alert_name: str


@action
def sampler(event: ExecutionBaseEvent, params: AlertManagerParams):
    logging.info(params.alert_name)


@action
def alert_manager_enricher(alert: PrometheusKubernetesAlert, params: AlertManagerURL):
    """
    Add a button to the alert - clicking it to silence the alert
    """
    alert_name = alert.alert.labels.get("alertname", "")
    if not alert_name:
        return

    alert.add_enrichment(
        [
            CallbackBlock(
                {
                    "Silence for 15 minutes": CallbackChoice(
                        action=sampler,
                        action_params=AlertManagerParams(
                            alert_name=f"{alert_name}",
                            alert_manager_url=params.alert_manager_url,
                        ),
                    )
                },
            )
        ]
    )