#!/usr/bin/env python3

import logging, hashlib, io, time
from request import Auth, UnlockRequest

logging.basicConfig(level=logging.WARNING)

use_fastboot = False

try:
    from adb.fastboot import FastbootCommands
    from adb.usb_exceptions import *
    fdev = FastbootCommands()
    try:
        fdev.ConnectDevice()
        use_fastboot = True
    except DeviceNotFoundError:
        logging.warning("No device detected in fastboot. Using manual mode.")
except ImportError:
    logging.warning("python-adb fastboot interface unavailable. Using manual mode.")

auth = Auth()
auth.login_tui("unlockApi")
logging.debug(auth.__dict__)

r = UnlockRequest(auth, "unlock.update.miui.com", "/api/v3/unlock/userinfo", {
  "data":{
    "uid":auth.userid,
    "clientId":"1",
    "clientVersion":"5.5.224.24",
    "language":"en",
    "pcId":hashlib.md5(auth.pcid.encode("utf-8")).hexdigest(),
    "region":"",
}})
r.add_nonce()
data = r.run()
logging.debug(data)
if not data["shouldApply"]:
    logging.error("Xiaomi server says shouldApply false, status %d", data["applyStatus"])
    input("Press Ctrl-C to cancel, or enter to continue. ")



mtkqcom = input("What is the SoC brand of the device you want to unlock? `mtk` for Mediatek, `qcom` for Qualcomm: ") # This is the worst way to implement this because i suck at everything

if mtkqcom == "mtk":
    if use_fastboot:
        product = fdev.Getvar("product").decode("utf-8")
        token = fdev.Oem("get_token").decode("utf-8")
        logging.debug("product is %s, token is %s", product, token)

    else:
        product = input("Enter output from `fastboot getvar product` (Ctrl-C to cancel): ")
        token = input("Enter output from `fastboot oem get_token` \nCombine the strings (left to right) then enter it here. (Ctrl-C to cancel): ")
        logging.debug("product is %s, token is %s", product, token)


elif mtkqcom == "qcom":
    if use_fastboot:
        product = fdev.Getvar("product").decode("utf-8")
        token = fdev.Getvar("token").decode("utf-8")
        logging.debug("product is %s, token is %s", product, token)

    else:
        product = input("Enter output from `fastboot getvar product` (Ctrl-C to cancel): ")
        token = input("Enter output from `fastboot getvar token` (Ctrl-C to cancel): ")
        logging.debug("product is %s, token is %s", product, token)


else:
    print("Invalid answer.")
    exit()



r = UnlockRequest(auth, "unlock.update.miui.com", "/api/v2/unlock/device/clear", {
  "appId":"1",
  "data":{
    "clientId":"1",
    "clientVersion":"5.5.224.24",
    "language":"en",
    "pcId":hashlib.md5(auth.pcid.encode("utf-8")).hexdigest(),
    "product":product,
    "region":"",
}})
r.add_nonce()
data = r.run()
logging.debug(data)
print(f"Xiaomi server says: {data['notice']} It says that the unlock will {'' if data['cleanOrNot'] else 'not '}wipe data.")
input("Press Ctrl-C to cancel, or enter to continue. ")

r = UnlockRequest(auth, "unlock.update.miui.com", "/api/v3/ahaUnlock", {
  "appId":"1",
  "data":{
    "clientId":"2", # updated client id
    "clientVersion":"5.5.224.24", # updated version number
    "language":"en",
    "operate":"unlock",
    "pcId":hashlib.md5(auth.pcid.encode("utf-8")).hexdigest(),
    "product":product,
    "region":"",
    "deviceInfo":{
      "boardVersion":"",
      "product":product,
      "socId":"",
      "deviceName":""
    },
    "deviceToken":token,
}})
r.add_nonce()
data = r.run()
logging.debug(data)

if use_fastboot:
    confirm = input("Acquired token! Do you want to unlock now? Enter `yes` or `no`:")

    if confirm == "yes":
        fdev.Download(io.BytesIO(bytes.fromhex(data["encryptData"])), len(bytes.fromhex(data["encryptData"])))
        time.sleep(0.5)
        fdev.Oem("unlock")

    else:
        print("Printing out unlock token.")
        print(data["encryptData"])

else:
    print("Done! Printing out unlock token.")
    print(data["encryptData"])
