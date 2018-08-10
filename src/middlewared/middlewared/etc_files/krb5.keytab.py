import logging
import os
import base64

from middlewared.utils import run
from freenasUI.common.pipesubr import pipeopen

logger = logging.getLogger(__name__)
kdir = "/etc/kerberos"
keytabfile = "/etc/krb5.keytab"
ktutil_cmd = "/usr/sbin/ktutil copy"

async def ktutil_copy(temp_keytab):
    p = pipeopen(f'{ktutil_cmd} {temp_keytab} {keytabfile}')
    output = p.communicate()
    if output[1]:
        logger.debug(f'generate krb5.keytab failed with error: {output[1]}')

async def write_keytab(db_keytabname, db_keytabfile):
    temp_keytab = f'{kdir}/{db_keytabname}'
    if not os.path.exists(kdir):
        os.mkdir(kdir)
    if os.path.exists(temp_keytab):
        os.remove(temp_keytab)
    with open(temp_keytab, "wb") as f:
        f.write(db_keytabfile)

    await ktutil_copy(temp_keytab)

async def render(service, middleware):
    keytabs = await middleware.call("datastore.query", "directoryservice.kerberoskeytab")
    if not keytabs:
        logger.debug(f'No keytabs in configuration database, skipping keytab generation')
        return

    for keytab in keytabs:
        db_keytabfile = base64.b64decode(keytab['keytab_file'])
        db_keytabname = keytab['keytab_name']
        await write_keytab(db_keytabname, db_keytabfile)

