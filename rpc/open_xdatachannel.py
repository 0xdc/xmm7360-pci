#!/usr/bin/env python3

from os.path import join, abspath, dirname
import uuid
import socket
import struct
import subprocess
import sys
import time

import rpc
import logging
# must do this before importing pyroute2
logging.basicConfig(level=logging.DEBUG)

r = rpc.XMMRPC()

r.execute('UtaMsSmsInit')
r.execute('UtaMsCbsInit')
r.execute('UtaMsNetOpen')
r.execute('UtaMsCallCsInit')
r.execute('UtaMsCallPsInitialize')
r.execute('UtaMsSsInit')
r.execute('UtaMsSimOpenReq')

rpc.do_fcc_unlock(r)
# disable aeroplane mode if had been FCC-locked. first and second args are probably don't-cares
rpc.UtaModeSet(r, 1)

apn = "everywhere"

r.execute('UtaMsCallPsAttachApnConfigReq',
          rpc.pack_UtaMsCallPsAttachApnConfigReq(apn), is_async=True)

attach = r.execute('UtaMsNetAttachReq',
                   rpc.pack_UtaMsNetAttachReq(), is_async=True)
_, status = rpc.unpack('nn', attach['body'])

if status == 0xffffffff:
    logging.info("Attach failed - waiting to see if we just weren't ready")

    timeout = 16
    while timeout > 0 and not r.attach_allowed:
        r.pump()
        timeout -= 1

    attach = r.execute('UtaMsNetAttachReq',
                       rpc.pack_UtaMsNetAttachReq(), is_async=True)
    _, status = rpc.unpack('nn', attach['body'])

    if status == 0xffffffff:
        logging.error("Attach failed again, giving up")
        sys.exit(1)

while True:
    ip_addr, dns_values = rpc.get_ip(r)
    if ip_addr is not None:
        break
    interval = 15
    logging.info(f"IP address couldn't be fetched, waiting {interval} seconds")
    time.sleep(interval)

logging.info("IP address: " + str(ip_addr))
logging.info("DNS server(s): " + ', '.join(map(str, dns_values['v4'] + dns_values['v6'])))

try:
    from pyroute2 import IPRoute
    ipr = IPRoute()

    idx = ipr.link_lookup(ifname='wwan0')[0]

    ipr.flush_addr(index=idx)
    ipr.link('set',
             index=idx,
             state='up')
    ipr.addr('add',
             index=idx,
             address=ip_addr)


    ipr.route('add',
              dst='default',
              priority=1000,
              oif=idx)
except ImportError:
    subprocess.run(["ip", "addr",  "flush", "dev", "wwan0"])
    subprocess.run(["ip", "link",  "set", "dev", "wwan0", "up"])
    subprocess.run(["ip", "addr",  "add", ip_addr, "dev", "wwan0"])
    subprocess.run(["ip", "route", "add", "default", "dev", "wwan0", "metric", "1024", "scope", "global"])

subprocess.run(["resolvectl", "dns", "wwan0"] + list(map(str, dns_values['v4'] + dns_values['v6'])))

# this gives us way too much stuff, which we need
pscr = r.execute('UtaMsCallPsConnectReq',
                 rpc.pack_UtaMsCallPsConnectReq(), is_async=True)
# this gives us a handle we need
dcr = r.execute('UtaRPCPsConnectToDatachannelReq',
                rpc.pack_UtaRPCPsConnectToDatachannelReq())

csr_req = pscr['body'][:-6] + dcr['body'] + b'\x02\x04\0\0\0\0'

r.execute('UtaRPCPSConnectSetupReq', csr_req)
