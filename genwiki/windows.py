import win32serviceutil, win32service, win32event, servicemanager

class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "WikiService"
    _svc_display_name_ = "Wiki Service"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        self.running = False
        self.p = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.running = False
        try:
            self.p.terminate()
        except Exception:
            pass
        finally:
            self.p = None

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_,''))
        self.main()

    def main(self):
        self.running = True
        while self.running:
            if not self.p:
                self.p = multiprocessing.Process(target=main, args=(False, 'e:\\alex\\Google Drive\\wiki\\wiki_alex.yaml'))
                self.p.start()
            elif self.p.is_alive():
                try:
                    time.sleep(1)
                except Exception:
                    pass


def run_as_windows_service():
    '''Runs the wiki as a windows service'''
    win32serviceutil.HandleCommandLine(AppServerSvc)

