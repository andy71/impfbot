
"""api wrapper for the lower saxony vaccination portal"""
import logging
import time
import json

from requests.sessions import Session
from requests.exceptions import ConnectionError as RequestConnectionError
from common import sleep

log = logging.getLogger(__name__)


class ShadowBanException(Exception):
    """Exception for ip ban detection"""


def fetch_api(
        zip_code: int,
        birthdate_timestamp: int = None,
        group_size: int = None,
        max_retries: int = 10,
        sleep_after_error: int = 30,
        jitter: float = 5,
        user_agent: str = 'python'
    ) -> any:
    """fetches the api with ip ban avoidance"""
    url = f"https://www.impfportal-niedersachsen.de/portal/rest/appointments/findVaccinationCenterListFree/{zip_code}?stiko="
    if birthdate_timestamp:
        url += f"&count=1&birthdate={int(birthdate_timestamp)*1000}"
    elif group_size:
        url += f"&count={group_size}"
    fail_counter = 0
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': user_agent
    }

    for fail_counter in range(0, max_retries+1):
        try:
            session = Session()
            with session.get(url=url, headers=headers, timeout=10) as data:
                fileprefix = time.strftime("%H-%M-%S")
                with open('/mnt/lvm_daten/tmp/impfbot/' + fileprefix + ".json", 'w') as jsonfile:
                    jsonfile.write(json.dumps(json.loads(data.text), indent=2, sort_keys=False, ensure_ascii=False).encode('utf8').decode('utf8'))
                return data.json()["resultList"]
        except RequestConnectionError as ex:
            raise ex
        except Exception as ex:
            log.debug(f"Exeption during request {ex}")
            sleep_time = sleep_after_error*fail_counter
            sleep(sleep_time, jitter)
    raise ShadowBanException
