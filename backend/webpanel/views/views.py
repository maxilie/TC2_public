import os
import pkgutil
import shutil
import sys
import time
import time as pytime
import traceback
from threading import Thread
from types import ModuleType

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from webpanel import apps, shared, api_util


@api_view(['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'PATCH', 'OPTIONS'])
@permission_classes([AllowAny])
def do_nothing(request, resource):
    """Displays nothing when someone makes a call to an invalid API endpoint."""
    return Response('Nothing here...',
                    status=status.HTTP_404_NOT_FOUND)


# TODO THE UPDATE FEATURE IS NOT USED - IT NEEDS MORE TESTING
# TODO IS IT USEFUL TO UPDATE ONLY THE tc2 MODULE AND NOT THE API?
@api_view(['GET'])
def update(request):
    """Stops the program, pulls latest code from GitHub, and restarts."""
    try:
        # Ignore the request if the program is already being updated
        if shared.program_starting.value:
            return Response('Program already starting/stopping/updating')
        else:
            shared.program_starting.value = True

        # Stop TC2Program
        if shared.program is not None:
            shared.program.shutdown()
            print('Program shutdown from endpoint: /api/update')
            time.sleep(0.2)

        # Remove old code files\
        import shutil
        try:
            shutil.rmtree('/tc2', ignore_errors=True)
            shutil.rmtree('/tmp_update_cache', ignore_errors=True)
            os.remove('/config.properties')
        except OSError:
            pass

        # Fetch new code files from GitHub
        os.mkdir('/tmp_update_cache')
        os.system('git clone https://maxilie:cc27fceff4cdd24ae84d5f9a5d48d0f74f2850d8@github.com/maxilie/TC2 '
                  '/tmp_update_cache')

        # Copy over new code files
        copytree('/tmp_update_cache/backend/tc2', '/tc2')
        shutil.move('/tmp_update_cache/backend/config.properties', '/config.properties')

        # Reload the python modules
        import tc2
        reload_package(tc2)

        # Create a new TC2Program object
        from tc2.TC2Program import TC2Program
        from tc2.log.LogFeed import LogFeed
        from tc2.log.LogFeed import LogCategory
        program: TC2Program = TC2Program(LogFeed(LogCategory.PROGRAM))

        # Save the new program in the django app
        apps.program = program

        # Start the program in a separate thread so as not to block the django view
        def start_logic():
            # Set environment's timezone to New York so logs are consistent
            os.environ['TZ'] = 'America/New_York'
            pytime.tzset()
            # Start the program
            program.start_program()
            shared.program_starting.value = False
            print('Started program with pid {}'.format(os.getpid()))

        init_thread = Thread(target=start_logic)
        init_thread.start()
    except Exception:
        api_util.log_stacktrace('updating the program', traceback.format_exc())
        shared.program_starting.value = False
        return Response('Error updating the program!')

    return Response('Successfully updated and restarted the program')


def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)


def unload_package(package):
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
        try:
            del sys.modules[package + '.' + modname]
        except Exception:
            pass


def reload_package(root_module):
    package_name = root_module.__name__

    # Get a reference to each loaded module
    loaded_package_modules = dict([
        (key, value) for key, value in sys.modules.items()
        if key.startswith(package_name) and isinstance(value, ModuleType)])

    # Delete references to these loaded modules from sys.modules
    for key in loaded_package_modules:
        del sys.modules[key]

    # Load new modules and share new state with old modules
    for key in loaded_package_modules:
        newmodule = __import__(key)
        oldmodule = loaded_package_modules[key]
        oldmodule.__dict__.clear()
        oldmodule.__dict__.update(newmodule.__dict__)
