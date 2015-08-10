"""
Distributed computing controller based on zmq.

    Copyright (C) 2014  James A. Lupo

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    jalupo@cct.lsu.edu  or  jalupo2009@gmail.com


There are 2 components provided by this script: 

   dispatcher ...... maintains queue of tasks, provides task data on
                     request, helps with job time awareness, and
                     initiates shutdown when no more work can be done.
   worker .......... continuously requests tasks from the dispatcher,
                     one at a time, until all tasks are completed or
                     job time runs out.

In a parallel environment, the dispatcher should be the first program
launched on the mother superior. Workers should then be launched on
all nodes, including the mother superior.

Work does not begin until the dispatcher receives and responds to a
request for a task assignment. Work will be handed out until the list
of tasks is exhausted or job time runs out.

Some of the important variables are:

  port .. Port for the dispatcher request socket (default: 5557)
  host .. Host name on which dispatcher is running.

"""

import time
import zmq
import getopt
import sys
import socket
import subprocess
from multiprocessing import Process
import re


def shell ( cmd ):
   """
   Submits a shell command for processing, and returns the cmd status
   flag plus the STDIN and STDOUT messages.

   Arguments:

      cmd .. The desired shell command line.

   Returns:

      3-tuple: True/False for success/failure.
               List of stdout lines.
               List of stderr lines.
   """
   p = subprocess.Popen( cmd, shell=True, stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE )
   x = p.communicate()
   p.stdout.close()
   p.stderr.close()
   if x[1] == '':
      status = True
   else:
      status = False
      
   return [ status, x[0].split( '\n' ), x[1].split( '\n' ) ]


def ipaddrs( host ):
   """
   Gets IP for host specified by name.

   Arguments:
    
      host .. Host name to look up.

   Returns:

      The named host's IP address.
   """
   return socket.gethostbyaddr(host)[2][0]


def dispatcher( port, cmd, files, allworkers, start ):
   """
   The dispatcher task, which is run as a separate thread, handles
   distribution of tasks to workers. Workers must request a task
   then wait for data to be sent in reply.

   Arguments:

      port ......... The socket on which to listen for work requests.
      cmd .......... Command for workers to execute.
      files ........ List of input files to distribute.
      allworkers ... Total number of workers (workers per node * nodes).
      start ........ The task number to start with - allows skipping
                     over completed tasks.

   The "dispatcher" reads a list of lines from an input file and
   constructs task messages for the workers. Workers must first issue
   a request to the dispatcher, which then replies with one task
   message.  When all work is handed out, or the first report of
   insufficient time is received, the dispatcher starts sending
   termination messages instead until all workers have been notified
   to cease. 

   The request message is a dictionary of:
       msg['worker'] ... name of worker making request.
       msg['maxtime'] .. the maximum execution time it has seen.
                         It is -1 if job time has run out.
       msg['lasttask'] . the most recent task the worker handled.

   The response message is a dictionary of:
       msg['cmd'] ...... The command to execute, or "FINI" to quit.
       msg['file'] ..... The next line read from the input file.
       msg['maxtime'] .. The longest task time seen so far.
       msg['tasknum'] .. The sequence number of the assigned task.

   """
   # Only the host running as dispatcher should be calling this.

   host = ipaddrs( socket.gethostname() )

   # Initialize a 0mq context

   context = zmq.Context()

   # Set up a socket to receive task requests and send replies over.
   # The linger option is set to help make sure all comunication is
   # delivered when the thread ends. The time unit is milliseconds.  A
   # rigorous receive request - send reply pattern must be followed as
   # the zmq.REP socket keeps track of who sent the request and thus
   # were the reply should go. Trying to do two receives or two sends
   # in a row will cause a fatal error or hang the program. Here we
   # set up the REP side of the socket pattern.

   dispatcher_socket = context.socket( zmq.REP )
   dispatcher_socket.setsockopt( zmq.LINGER, 5000 )
   dispatcher_socket.bind( "tcp://%s:%s" % ( host, port ) )

   maxtime = 0
   tasknum = 0
   workers = {}
   already_notified = 0

   sys.stderr.write ( "Dispatcher:Start:%d\n" % ( start ) )
   sys.stderr.flush()

   # Adjust starting task for 0 offset:

   start = start - 1
   tasknum = start
   lasttask = 0

   for f in files[start:]:

      request = dispatcher_socket.recv_json()
      worker = request['worker']
      workers[worker] = 1

      # Interpret a negative maxtime value as the time up signal.

      if request['maxtime'] >= 0 :

         if request['maxtime'] > maxtime :

            maxtime = request['maxtime']
            sys.stderr.write( "Dispatcher:Maxtime:%s:%.2f:%.2f\n"
                              % ( worker, maxtime, time.time() ) )
            sys.stderr.flush()

         tasknum = tasknum + 1
         task_message = { 'cmd' : cmd, 'file' : f.strip(),
                          'maxtime' : maxtime, 'tasknum' : tasknum }

      else:

         maxtime = -1
         sys.stderr.write( "Dispatcher:Timeup:%s:%.2f\n"
                           % ( worker, time.time() ) )
         sys.stderr.flush()
         task_message = { 'cmd' : "FINI", 'file' : "None",
                          'maxtime' : -1, 'tasknum' : tasknum }
         already_notified += 1
         lasttask = request['lasttask']

      dispatcher_socket.send_json( task_message )
      if maxtime < 0 :
         break

   # Now make sure all workers have received the shutdown message.

   shutdown = allworkers - already_notified

   if lasttask == 0 :
      # All tasks handed out before any completions received.
      # Have to assume all will complete.
      lasttask = tasknum

   if shutdown > 0 :
      task_message = { 'cmd' : "FINI", 'file' : "None",
                       'maxtime' : -1, 'tasknum' : tasknum }
      sys.stderr.write( "Dispatcher:Shutdown:%d\n" % ( shutdown ) )
      sys.stderr.flush()

      # There is always a chance multiple assignments went out before
      # a timeout was received. All should sense time out as well,
      # so check for that when handling their final requests.

      for w in range( shutdown ):

         request = dispatcher_socket.recv_json()

         if request['maxtime'] < 0 :
            if request['lasttask'] < lasttask :
               lasttask = request['lasttask']

         dispatcher_socket.send_json( task_message )

   sys.stderr.write( "Dispatcher:Last:%d\n" % ( lasttask ) )
   sys.stderr.flush()


def worker( wrk_num, host, port, jobtime ):
   """
   Defines the worker task. The arguments include:

      wrk_num .. Identifier for the worker on a node.
      host ..... IP of host running the dispatcher.
      port ..... The dispatcher port.
      jobtime .. How many seconds available for all work.

   The "worker" sends a task request message via a zmq.REQ socket to
   the dispatcher, and waits for a reply. Each reply is a dictionary
   containing a command name and an input file. If the command is not
   the termination command, the task is executed and the result is sent
   down  zmq.PUSH connection to the results manager.

   A "task" is defined in a dictionary set by the dispatcher, and the
   results are returned in a second dictionary.  Obviously, the keys
   must agree on both ends. See dispatcher above for a description
   of the request and reply messages.
   """
   # For safety, require the remaining time to be at least 1.25 times
   # the maximum time seen so far to account for some jitter in the
   # task times.

   margin = 1.25

   # Get our host name.

   local = socket.gethostname()

   # Get a starting time hack (in seconds since the epoc).

   starttime = time.time()

   # Initialize a zeromq context

   context = zmq.Context()

   # Set up a socket for communication with the dispatcher. This
   # is the requestor side of the REQ/REP pattern.

   task_socket = context.socket( zmq.REQ )
   task_socket.connect( "tcp://%s:%s" % ( host, port ) )
   task_poller = zmq.Poller()
   task_poller.register( task_socket, zmq.POLLIN )

   # Prepare to keep track of the longest running task. Initialize
   # variables just in case they are used before otherwise set.

   maxtime = 0
   timeout = 100
   running = True
   workerID = "%s_%d" % ( local, wrk_num )
   tasknum = 0
   walltime = 0
   timeup = False

   while running:

      # Send a task request to the displatcher, or report time is up by
      # setting maxtime to a negative value.

      if timeup :
         task_socket.send_json( { 'maxtime' : -1.0, 'worker' : workerID,
                                  'lasttask' : tasknum } )
      else:
         task_socket.send_json( { 'maxtime' : maxtime, 'worker' : workerID,
                                  'lasttask' : tasknum } )

      socks = dict( task_poller.poll( timeout ) )

      if socks.get( task_socket ) == zmq.POLLIN:

         # Looks like we received a task. Process it.

         task_message = task_socket.recv_json()

         if task_message['cmd'] != "FINI" :

            # Construct the command line.

            task = "%s %s" % ( task_message['cmd'], task_message['file'] )

            # Deal with job time calculation.

            if task_message['maxtime'] > maxtime:
               maxtime = task_message['maxtime']

            tasknum = task_message['tasknum']
            walltime = time.time() - starttime
            timeleft = jobtime - walltime

            # Apply the margin of error and decide to execute or skip.

            if timeleft > ( maxtime * margin ):

               sys.stderr.write( "%s:%s:%d:%.2f:%.2f\n"
                                 % ( workerID, "Taking", tasknum,
                                     walltime, timeleft ) )
               sys.stderr.flush()

               # Record how long the task takes.

               taskstart = time.time()
               result = shell( task )
               taskend = time.time()
               elapsed = taskend - taskstart
               walltime = taskend - starttime

               if elapsed > maxtime:
                  maxtime = elapsed

               results = {
                  'worker' : workerID,
                  'mode' : "Ran",
                  'tasknum' : tasknum,
                  'task' : task,
                  'taskstart' : taskstart,
                  'taskend' : taskend,
                  'tasktime' : elapsed,
                  'walltime' : walltime,
                  'status' : result[0],
                  'stdout' : result[1],
                  'stderr' : result[2] }

            else:

               timeup = True

               sys.stderr.write(
                  "%s:%s:%d:%.2f:%.2f\n" % ( workerID, "Skipping", tasknum,
                                             walltime, timeleft ) )
               sys.stderr.flush()

               results = {
                  'worker' : workerID,
                  'mode' : "Skipped",
                  'tasknum' : tasknum,
                  'task' : task,
                  'taskstart' : -1.0,
                  'taskend' : -1.0,
                  'tasktime' : -1.0,
                  'walltime' : walltime,
                  'status' : False,
                  'stdout' : [ 'Insufficient Time', '' ],
                  'stderr' : [ 'Time left: %.2f; Max Time: %.2f; Margin: %.2f' %
                               ( timeleft, maxtime, margin ), '' ] }

            print_results( results )

         else:

            running = False


def print_results( results ):
   """
   Procedure to print out results. The argument is a dictionary:

      'worker' : The worker identifier.
      'mode' : "Ran" or "Skipped".
      'tasknum' : The task number.
      'task' : The task command line string.
      'taskstart' : task start time, or -1.0.
      'taskend' : task end time, or -1.0.
      'tasktime' : elapsed time for task, or -1.0.
      'walltime' : the current job walltime.
      'status' : task execution status.
      'stdout' : task standard output.
      'stderr' : task standard error.
   """

   print( "Task:%d:%s:%s:%s:%s\n"
          % ( results['tasknum'],
              results['worker'],
              results['mode'],
              results['status'],
              results['task'] )
          + "Timings:%d:%s:%.2f:%.2f:%.2f:%.2f\n"
          % ( results['tasknum'],
              results['worker'],
              results['taskstart'],
              results['taskend'],
              results['tasktime'],
              results['walltime'] )
          + "Stdout:%d:" % (results['tasknum']) )
   for l in results['stdout']:
      if len( l.strip() ) > 0:
         print( "  %s" % ( l.strip() ) )
   print( "Stderr:%d:" % (results['tasknum']) )
   for l in results['stderr']:
      if len( l.strip() ) > 0:
         print( "  %s" % ( l.strip() ) )
   print( '' )
   sys.stdout.flush()


def Usage():
   global jobtime
   print( """
Usage:  python wq.py -h[--help]
        python [-s[--start] task_num ] -d[--dispatcher] cmd \
               -a[--allworkers] n -i[--input] filenm
        python -w[--workers] n -m[--mothersuperior] ms [-t[--time] walltime] 
   Help display:
      -h,--help ........ Display this help message.
   Run as dispatcher:
      -s,--start task_num .. Task number to start with. Represents the line
                             number in the input list file. Default is 1.
      -d,--dispatcher cmd .. Run as the dispatcher for the command cmd, where
                             cmd is the command or script to use for the task.
                             cmd will be called with a single file path as
                             it's only argument.
      -i,--inputs filenm ... Name of file containing input file names to
                             serve as inputs to cmd, one per task.
      -a,--allworkers n .... Total workers ( workers per node * nodes ).
   Run as worker:
      -w,--workers n ........... Run n workers per node.
      -m,--mothersuperior ms ... Host name of mother superior node.
      -t,--time walltime ....... Wallclock time to allow for entire job.
                                 May be expressed as one of the following:
                                    ss, mm:ss, hh:mm:ss, or d:hh:mm:ss.
                                 (note: Torque sets env variable PBS_WALLTIME)

   The dispatcher must be started before any of the workers.
""" )
   print( "   The default worker jobtime is hardwired to %d secs - 1 day.\n"
          % ( jobtime ) )
   print( "   Revision: $Id: wq.py 143 2014-07-30 16:51:30Z jalupo $\n" )


def time2secs( s ):
   """
   Convert time in a string to seconds.

   Args:

      s .. time string. May be 'ss', 'mm:ss', 'hh:mm:ss', 'd:hh:mm:ss'

   Returns:

      Number of seconds as an int.
   """
   t = s.split( ':' )
   nf = len( t )
   if nf == 1:
      # Seconds only!
      secs = int( t[0] )
   elif nf == 2:
      # Minutes & seconds!
      secs = int( t[1] ) + int( t[0] ) * 60
   elif nf == 3:
      # Hours, minutes & seconds!
      secs = int( t[2] ) + int( t[1] ) * 60 + int( t[0] ) * 60 * 60   
   elif nf == 4:
      # Days, hours, minutes, & seconds!
      secs = int( t[3] ) + int( t[2] ) * 60 + int( t[1] ) * 60 * 60
      secs += int( t[0] ) * 60 * 60 * 24

   return secs


# And here is the main line.

if __name__ == "__main__":

   global jobtime

   port = '54321'
   start = 1
   jobtime = 86400
   filenm = ''
   ms = ''

   try:

      opts, args = getopt.getopt( sys.argv[1:], "hd:w:s:i:t:m:a:",
                                  ['help', 'dispatcher=', 
                                   'workers=', 'start=', 'inputs=',
                                   'time=', 'mothersuperior=',
				   'allworkers='] )

   except getopt.GetoptError, err:

      print str( err )
      Usage()
      sys.exit( 2 )

   for o, a in opts:

      if o in ( "-d", "--dispatcher" ) :

         mode = 'd'
         cmd = a

      elif o in ( "-w", "--workers" ) :

         mode = 'w'
         numw = int( a )

      elif o in ( "-a", "--allworkers" ) :

         allw = int( a )

      elif o in ( "-s", "--start" ) :

         start = int ( a )

      elif o in ( "-i", "--inputs" ) :

         filenm = a

      elif o in ( "-m", "--mothersuperior" ) :

         ms = a

      elif o in ( "-t", "--time" ) :

         jobtime = time2secs( a )

      elif o in ( "-h", "--help" ) :

         Usage()
         sys.exit( 0 )

      else:

	 print( "ERROR: Unknown option: \"%s\"" % ( o ) )
         print( "Run with -h or --help for usage hints." )
         sys.exit( 1 )

   if mode == 'w':

      if ms == '' :
         print( "ERROR: Mother superior host name not specified." )
         print( "Run with -h or --help for usage hints." )
         sys.exit( 1 )

      if numw < 1 :
         print( "ERROR: Number of workers must be positive! Have: %d" % \
                ( numw ) )
         sys.exit( 1 )

      if jobtime < 1 :
         print( "ERROR: --jobtime must be positive! Have: %d" % ( jobtime ) )
         sys.exit( 1 )

      # Get hostname of mother superior node.

      host = ipaddrs( ms )

      # Launch the desired number of worker threads.

      for wrk_num in range( numw ):

         Process( target = worker,
                  args = ( wrk_num, host, port, jobtime ) ).start()

   if mode == 'd':

      if allw < 1 :
         print( "ERROR: --allworkers must be positive! Have: %d" % \
                ( allw ) )
         sys.exit( 1 )

      # Open the input list file.

      try:
         infile = open( filenm, 'r')
      except IOError:
         print( "ERROR: Failed to open inputs file: \"%s\"" % ( filenm ) )
         sys.exit( 1 )

      files = infile.readlines()
      infile.close()
      tasks = len( files )

      # Fire up the dispatcher!

      if start > tasks:
         print( "ERROR: Starting point (%d) exceeds input lines (%d)!" %
                ( start, tasks ) )
         sys.exit( 1 )

      if tasks > 0:
         dispatcher = Process( target = dispatcher,
                               args = ( port, cmd, files, allw, start ) )
         dispatcher.start()
      else:
         print( "ERROR: Inputs file appears empty: \"%s\"" % ( filenm ) )
         sys.exit( 1 )

# And we're out'a here!
