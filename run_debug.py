import sys, logging, uvicorn
print('stderr closed before:', getattr(sys.stderr,'closed', None))
root = logging.getLogger()
print('root handlers:', root.handlers)
for h in root.handlers:
    print('handler stream closed?', getattr(getattr(h, "stream", None), "closed", None))
uvicorn.run('app:app', port=8000, reload=False)
