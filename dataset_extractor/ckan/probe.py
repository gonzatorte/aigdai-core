from ckanapi import RemoteCKAN, ServerIncompatibleError

def probe(base_url: str) -> bool:
    # ToDo: Could work to create a probe
    try:
        site = RemoteCKAN(base_url, get_only=True)
        site.action.site_read()
    except ServerIncompatibleError:
        return False
    return True

if __name__ == '__main__':
    probe('')
