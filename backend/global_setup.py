HOST = '127.0.0.1'

#sprawdzać porty, socket może próbować otwierać na zajętych

BACK_FRONT_HISTORYREQUESTS_PORT = 65432  #back -> front htttp traffic tab, requests
BACK_FRONT_SCOPEREQUESTS_PORT = 65433  # back -> front scope tab, requests
FRONT_BACK_DROPREQUEST_PORT = 65434 # front -> back, drop request
FRONT_BACK_SCOPEUPDATE_PORT = 65430# front -> back, scope update
FRONT_BACK_FORWARDBUTTON_PORT = 65436 # front -> back, forward button
FRONT_BACK_INTERCEPTBUTTON_PORT = 65437 # front -> back, intercept button
REPEATER_BACK_SENDHTTPMESSAGE_PORT = 65438 # repeater -> back, send button
FRONT_BACK_SENDTOREPEATER_PORT = 65439 # front -> back,  send flag to proxy.py
BACK_REPEATER_FLOWSEND_PORT = 65440 # back-> repeater, send flow to Gui repeater
BACK_REPEATER_RESPONSESEND_PORT = 65441 # back -> repeater, send response to repeater