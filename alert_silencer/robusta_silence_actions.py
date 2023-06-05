import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Union

import requests
from robusta.api import (
    ActionParams,
    CallbackBlock,
    CallbackChoice,
    ExecutionBaseEvent,
    Finding,
    JsonBlock,
    PrometheusKubernetesAlert,
    action,
)


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
    # Format alert labels
    label_matchers: Union[List[Dict[Any, Any]], None] = []
    for i, (k, v) in enumerate(params.alert_labels.items()):
        label_matchers.append(
            {"name": k, "value": v, "isRegex": False, "isEqual": True}
        )

    # Post a silence rule
    response = requests.post(
        f"{params.alert_manager_url}/api/v2/silences",
        json={
            "matchers": label_matchers,
            "startsAt": datetime.utcfromtimestamp(time.time()).isoformat(),
            "endsAt": datetime.utcfromtimestamp(
                time.time() + params.silence_interval * 3600
            ).isoformat(),
            "createdBy": "robusta-silencer",
            "comment": f"Silence for {params.silence_interval}h",
        },
    )
    response.raise_for_status()

    logging.info(
        f"Successfully silenced alert with labels: {params.alert_labels} for {params.silence_interval}h"
    )

    # Create the finding
    finding = Finding(
        title="*Successfully silenced alert*", aggregation_key="alertmanager_silencer"
    )

    message: Dict[Any, Any] = {}
    message["blocks"] = [
        {"type": "header", "text": {"type": "mrkdwn", "text": "Sample text !!!!"}}
    ]
    message["attachments"] = {
        "fallback": "Plain-text summary of the attachment.",
        "color": "#2eb886",
        "pretext": "Optional text that appears above the attachment block",
        "author_name": "Bobby Tables",
        "author_link": "http://flickr.com/bobby/",
        "author_icon": "http://flickr.com/icons/bobby.jpg",
        "title": "Slack API Documentation",
        "title_link": "https://api.slack.com/",
        "text": "Optional text that appears within the attachment",
        "fields": [{"title": "Priority", "value": "High", "short": False}],
        "image_url": "http://my-website.com/path/to/image.jpg",
        "thumb_url": "http://example.com/path/to/thumb.png",
        "footer": "Slack API",
        "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
        "ts": "123456789",
    }

    # for i, (k, v) in enumerate(params.alert_labels.items()):
    #     message += f"* {k} : `{v}` \n"

    js = json.dumps(message)
    finding.add_enrichment([JsonBlock(js)])
    event.add_finding(finding)


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
