import os
import sys

os.chdir(r'D:\projects\acesi')
sys.path.insert(0, r'D:\projects\acesi')
import server

ok, msg = server.check_email_now(force_all=True)
print('ok:', ok)
print('msg:', msg)
