import logging

from robusta.api import action, PrometheusKubernetesAlert, ActionParams, CallbackBlock, CallbackChoice, ExecutionBaseEvent


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
def silence_enricher(alert: PrometheusKubernetesAlert, params: AlertManagerURL):
    """
    Add a button to the alert - clicking it to silence the alert
    """
    alert_name = alert.alert.labels.get("alertname", "")
    if not alert_name:
        return

    logging.info(alert.alert.labels)
    logging.info(alert_name)
    logging.info(params.alert_manager_url)
