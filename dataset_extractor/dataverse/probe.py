import socket
import httpx
import json
from urllib.parse import urlparse
from typing import Union


async def probe(base_url: str) -> Union[bool, None]:
    try:
        # ToDo: Take domain name from base_url, not whole string, and trim slashes
        parsed_url = urlparse(base_url)
        url = "%s://%s/api/info/version" % (parsed_url.scheme, parsed_url.hostname)
        async with httpx.AsyncClient(verify=False, timeout=15) as client:
            response = await client.get(url)
        if response.status_code != 200:
            return False
        try:
            result = json.loads(response.content)
        except json.decoder.JSONDecodeError:
            return False
        return result['status'] == 'OK'
    except socket.gaierror:
        return False
    except BaseException as err:
        print(err)
        return None


if __name__ == '__main__':
    probe('')
