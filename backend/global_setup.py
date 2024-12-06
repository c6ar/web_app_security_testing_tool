HOST = '127.0.0.1'

#sprawdzać porty, socket może próbować otwierać na zajętych

BACK_FRONT_HISTORYREQUESTS_PORT = 65432  #back -> front htttp traffic tab, requests
BACK_FRONT_SCOPEREQUESTS_PORT = 65433  # back -> front scope tab, requests
FRONT_BACK_DROPREQUEST_PORT = 65434 # front -> back, drop request
FRONT_BACK_SCOPEUPDATE_PORT = 65430# front -> back, scope update
FRONT_BACK_FORWARDBUTTON_PORT = 65436 # front -> back, forward button


#TODO   File "C:\Users\zioma\AppData\Local\Programs\Python\Python312\Lib\site-packages\mitmproxy\net\encoding.py", line 71, in decode
#    raise ValueError(
# ValueError: BadGzipFile when decoding b'{" ping_i with 'gzip': BadGzipFile('Not a gzipped file (b\'{"\')')