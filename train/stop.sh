ps -ef|grep MainCpp.py | awk '{print $2}' | xargs kill
ps -ef|grep multiprocessing | awk '{print $2}' | xargs kill