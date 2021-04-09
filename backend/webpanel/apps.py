import os
import traceback
from multiprocessing import Process
from threading import Thread
import time as pytime

from django.apps import AppConfig

from tc2.startup_task.DumpAIDataTask import DumpAIDataTask
from webpanel import shared


class WebpanelAppConfig(AppConfig):
    name = 'webpanel'
    verbose_name = "Webpanel"

    def ready(self):
        """
        Called when the Django backend starts.
        Starts a TC2Program.
        """

        # Create a new TC2Program object.
        from tc2.TC2Program import TC2Program
        from tc2.log.LogFeed import LogFeed
        from tc2.log.LogFeed import LogCategory

        if shared.program is not None:
            print('DJANGO RE-BOOTED BUT PROGRAM IS ALREADY RUNNING')
            return

        shared.program = TC2Program(LogFeed(LogCategory.PROGRAM))

        shared.program_starting.value = True

        # Start the program in a separate process.
        def start_logic():

            # Set environment's timezone to New York so logs are consistent.
            os.environ['TZ'] = 'America/New_York'
            pytime.tzset()

            # Start the program.
            shared.program.start_program()
            shared.program_starting.value = False
            print('Started program with pid {}'.format(os.getpid()))

            # STARTUP TASKS (single-run): Run each task once in another thread.
            try:
                print('Running startup debug task(s) in another thread')
                shared.program.info_main('Running startup debug task(s) in another thread')
                task = DumpAIDataTask(shared.program)
                debug_thread_2 = Thread(target=task.run)
                debug_thread_2.start()
            except Exception:
                shared.program.error_main('Error running startup debug tasks:')
                shared.program.warn_main(traceback.format_exc())

        program_process = Thread(target=start_logic)
        program_process.start()
