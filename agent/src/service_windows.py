"""
Windows Service Wrapper for Device Inventory Agent

Allows the agent to run as a Windows Service.
Requires pywin32: pip install pywin32
"""
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
except ImportError:
    print("pywin32 is required for Windows service support.")
    print("Install with: pip install pywin32")
    sys.exit(1)

from agent.src.agent import InventoryAgent

logger = logging.getLogger('inventory-agent-service')


class InventoryAgentService(win32serviceutil.ServiceFramework):
    """Windows Service wrapper for Inventory Agent."""

    _svc_name_ = 'InventoryAgent'
    _svc_display_name_ = 'Device Inventory Agent'
    _svc_description_ = 'Collects device and monitor information for IT inventory management.'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.agent = None

    def SvcStop(self):
        """Called when the service is being stopped."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        if self.agent:
            self.agent.stop()

        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        """Called when the service is being started."""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )

        self.main()

    def main(self):
        """Main service loop."""
        try:
            # Configure logging for service
            log_path = os.path.join(
                os.environ.get('PROGRAMDATA', 'C:\\ProgramData'),
                'InventoryAgent',
                'logs',
                'service.log'
            )
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_path)
                ]
            )

            # Config path
            config_path = os.path.join(
                os.environ.get('PROGRAMDATA', 'C:\\ProgramData'),
                'InventoryAgent',
                'config.json'
            )

            # Create and start agent
            self.agent = InventoryAgent(config_path=config_path)
            self.agent.start()

        except Exception as e:
            servicemanager.LogErrorMsg(f"Service failed: {e}")
            logger.error(f"Service failed: {e}", exc_info=True)


def install_service():
    """Install the Windows service."""
    try:
        win32serviceutil.InstallService(
            None,
            InventoryAgentService._svc_name_,
            InventoryAgentService._svc_display_name_,
            startType=win32service.SERVICE_AUTO_START,
            description=InventoryAgentService._svc_description_
        )
        print(f"Service '{InventoryAgentService._svc_display_name_}' installed successfully.")
        print("Start with: net start InventoryAgent")
    except Exception as e:
        print(f"Failed to install service: {e}")
        sys.exit(1)


def remove_service():
    """Remove the Windows service."""
    try:
        win32serviceutil.RemoveService(InventoryAgentService._svc_name_)
        print(f"Service '{InventoryAgentService._svc_display_name_}' removed successfully.")
    except Exception as e:
        print(f"Failed to remove service: {e}")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Running as service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(InventoryAgentService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Command line
        if sys.argv[1] == 'install':
            install_service()
        elif sys.argv[1] == 'remove':
            remove_service()
        else:
            win32serviceutil.HandleCommandLine(InventoryAgentService)
