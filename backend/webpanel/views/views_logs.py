import os
import traceback
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from webpanel import api_util, shared


@api_view(['GET'])
def logfeed_filenames(request):
    """Returns a list of logfile names for the given logfeed (excluding file extensions)."""
    from tc2.TC2Program import TC2Program
    from tc2.log.LogFeed import LogCategory

    # Extract parameters
    if 'logfeed' not in request.GET:
        return Response('You must specify a logfeed, i.e. /api/logs/logfeed_filenames/?logfeed=PROGRAM',
                        status=status.HTTP_400_BAD_REQUEST)
    logfeed_name = request.GET['logfeed']
    log_category = LogCategory(logfeed_name)
    if log_category is None:
        return Response(f'Invalid logfeed specified: "{logfeed_name}"',
                        status=status.HTTP_400_BAD_REQUEST)

    # Fetch the program instance
    program: TC2Program = shared.program

    # Get the logfeed corresponding to the log category
    if log_category == LogCategory.PROGRAM:
        logfeed = program.logfeed_program
    elif log_category == LogCategory.DATA:
        logfeed = program.logfeed_data
    elif log_category == LogCategory.LIVE_TRADING:
        logfeed = program.logfeed_trading
    elif log_category == LogCategory.OPTIMIZATION:
        logfeed = program.logfeed_optimization
    elif log_category == LogCategory.API:
        logfeed = program.logfeed_api
    elif log_category == LogCategory.VISUALS:
        logfeed = program.logfeed_visuals
    else:
        return Response(f'Invalid logfeed specified: "{logfeed_name}"',
                        status=status.HTTP_400_BAD_REQUEST)

    # Get names of files in the logfeed's folder
    filenames = []
    try:
        # Add raw filenames to a list.
        with logfeed.lock:
            for filename in os.listdir(logfeed.logDir):
                filenames.append(os.path.basename(filename).split('.txt')[0])

        # Define method to order 2020-01-04_15.txt as earlier than 2020-01-04_2.txt.
        def filename_to_date(filename):
            date_comp = filename.split('_')[0]  # returns e.g. '2020-01-04'
            date_order = int(filename.split('_')[1].split('.')[0])  # returns e.g. 15
            file_datetime = datetime.strptime(date_comp, '%Y-%m-%d') + timedelta(seconds=date_order)
            return file_datetime

        # Order the filenames chronologically.
        filenames.sort(key=lambda filename: filename_to_date(filename))
    except Exception:
        api_util.log_stacktrace('fetching logfeed filenames', traceback.format_exc())
    return Response(filenames)


@api_view(['GET'])
def logfile(request):
    """Displays the logfile (must start with directory like 'program/...' and exclude the file extension)."""

    # Extract parameters
    if 'filename' not in request.GET:
        return Response('You must specify a filename, i.e. /api/logs/logfile/?filename=program/2019-01-01_0',
                        status=status.HTTP_400_BAD_REQUEST)
    else:
        filename = request.GET['filename']

    # Get lines from the logfile
    lines = []
    try:
        filename = 'logs/' + filename + '.txt'
        file = open(filename, 'a+')
        file.seek(0)
        for line in file:
            lines.append(line.replace('\n', '').strip())
        file.close()
    except Exception as e:
        return Response('Error reading file: "{}"'.format(filename),
                        status=status.HTTP_400_BAD_REQUEST)
    return Response(lines)


@api_view(['GET'])
def latest_messages(request):
    """Displays the latest messages for the specified log feed."""
    from tc2.TC2Program import TC2Program
    from tc2.log.LogFeed import LogCategory

    # Extract parameters
    if 'logfeed' not in request.GET:
        return Response('You must specify a logfeed, i.e. /api/logs/latest/?logfeed=PROGRAM',
                        status=status.HTTP_400_BAD_REQUEST)
    logfeed_name = request.GET['logfeed']
    log_category = LogCategory(logfeed_name)
    if log_category is None:
        return Response(f'Invalid logfeed specified: "{logfeed_name}"',
                        status=status.HTTP_400_BAD_REQUEST)

    # Fetch the program instance
    program: TC2Program = shared.program

    # Get the logfeed corresponding to the log category
    if log_category == LogCategory.PROGRAM:
        logfeed = program.logfeed_program
    elif log_category == LogCategory.DATA:
        logfeed = program.logfeed_data
    elif log_category == LogCategory.LIVE_TRADING:
        logfeed = program.logfeed_trading
    elif log_category == LogCategory.OPTIMIZATION:
        logfeed = program.logfeed_optimization
    elif log_category == LogCategory.API:
        logfeed = program.logfeed_api
    elif log_category == LogCategory.VISUALS:
        logfeed = program.logfeed_visuals
    else:
        return Response(f'Invalid logfeed specified: "{logfeed_name}"',
                        status=status.HTTP_400_BAD_REQUEST)

    # Get lines from the logfile
    lines = []
    with logfeed.lock:
        file = logfeed.get_latest_logfile()
        for line in file:
            lines.append(line.replace('\n', '').strip())
        file.close()
    return Response(lines)


@api_view(['GET'])
def clear_logs(request):
    """Clears the log files."""
    from tc2.log.LogFeed import LogCategory
    from tc2.log.LogFeed import LogLevel

    try:
        # Delete log files
        for log_category in LogCategory:
            os.system(f'rm -rf logs/{log_category.value}')

        # Print a log message
        shared.program.logfeed_program.log(LogLevel.INFO, 'Cleared program log feed')
        shared.program.logfeed_data.log(LogLevel.INFO, 'Cleared data log feed')
        shared.program.logfeed_trading.log(LogLevel.INFO, 'Cleared trading log feed')
        shared.program.logfeed_optimization.log(LogLevel.INFO, 'Cleared optimization log feed')
        shared.program.logfeed_api.log(LogLevel.INFO, 'Cleared api log feed')
        shared.program.logfeed_visuals.log(LogLevel.INFO, 'Cleared visuals log feed')
    except Exception:
        return Response('Error clearing log files!')
    return Response('Successfully cleared log files')
