"""
Distributed computing controller based on 0mq.

There are 3 components: 

   dispatcher ...... maintains queue of tasks, provides task data on request.
   worker .......... requests one set of task data per request.
   result_manager .. Gathers results and helps with shutdown.

In a parallel environment, dispatcher and result_manager should be launched
on the mother superior. Workers can be launched on all other nodes.

The zmq socket implementation uses opportunistic binding, so the order of
startup is not important. Work does not begin until the dispatcher starts
handing out task information.

This script was motivated by the 0mq "distributed-computing" example
provided at:

  http://taotetek.net/2011/02/02/python-multiprocessing-with-zeromq/

The blog describes a script for each function. The functions were 
combined to help streamline use in batch scripts.

The important port and host variables are:

  dport ... Port for the dispatcher request socket (default: 5557)
  cport ... Port for the result_manager control socket (default: 5559)
  rport ... Port for the result_manager result socket (default: 5558)
  host .... Host name on which dispatcher is running.

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
   flag and both the STDIN and STDOUT messages.

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
    Gets IP for host specified by name. Needs a single argument:
    
       host .. Host name to look up.
    """
    return socket.gethostbyaddr(host)[2][0]


def dispatcher( dport, cmd, files ):
    """
    The dispatcher task. Arguments include:

       dport .. The socket on which to listen for work requests.
       cmd .... Command for workers to execute.
       files .. List of input files to distribute.

    The "dispatcher" function generates a list of commands and input
    files, and sends them down a zeromq "PUSH" connection to be processed
    by listening workers, in a round robin load balanced fashion.

    "Tasks" are defined by loading up a dictionary and sending it to
    the requesting worker, and results are returned as a second
    dictionary.  Obviously, the keys must agree on both ends.
    """
    # Only the host running as dispatcher should be calling this.

    host = ipaddrs( socket.gethostname() )

    # Initialize a zeromq context

    context = zmq.Context()

    # Set up a channel to send work messages over.

    dispatcher_send = context.socket( zmq.PUSH )
    dispatcher_send.bind( "tcp://%s:%s" % ( host, dport ) )

    # Give everything a second to spin up and connect

    time.sleep( 1 )

    # Load up the dispatcher with task messages.

    for f in files:
        work_message = { 'cmd' : cmd, 'file' : f.strip() }
        dispatcher_send.send_json( work_message )

    time.sleep( 1 )


def worker( wrk_num, host, dport, rport, cport, jobtime ):
    """
    Defines the worker task. The arguments include:

       wrk_num ... Identifier for the worker.
       host ...... IP of host running the dispatcher.
       dport ..... The dispatcher port.
       rport ..... The result_manager port.
       cport ..... The control message port.
       jobtime ... How many seconds available for all work.

    The "worker" function listens on a zeromq PULL connection for "work"
    from the dispatcher. Each is a dictionary containing a command name
    and an input file. The result is sent down another zeromq PUSH
    connection to the results manager. A "task" is defined in a dictionary
    set by the dispatcher, and the results are returned in a second
    dictionary.  Obviously, the keys must agree on both ends.

    The result manager takes a best effort approach to tracking and
    reporting the maximum execution time to all works over the control
    channel. There is no attempt at rigorous coherence.
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

    # Set up a channel to receive work from the dispatcher

    work_receiver = context.socket( zmq.PULL )
    work_receiver.connect( "tcp://%s:%s" % ( host, dport ) )

    # Set up a channel to return result of work to the results reporter

    results_sender = context.socket( zmq.PUSH )
    results_sender.connect( "tcp://%s:%s" % ( host, rport ) )

    # Set up a channel to receive control messages over. These include
    # updates to the maximum execution time seen.

    control_receiver = context.socket( zmq.SUB )
    control_receiver.connect( "tcp://%s:%s" % (host, cport ) )
    control_receiver.setsockopt( zmq.SUBSCRIBE, "" )

    # Set up a poller for the work and control receiver channels

    work_poller = zmq.Poller()
    work_poller.register( work_receiver, zmq.POLLIN )
    control_poller = zmq.Poller()
    control_poller.register( control_receiver, zmq.POLLIN )

    # Prepare to keep track of the longest running task.

    maxtime = 0

    # Loop and accept messages from both channels, acting accordingly.
    # http://zeromq.github.io/pyzmq/api/zmq.html indicates the timeout
    # values used in zmq.poller are in milliseconds, not microseconds.

    timeout = 1

    running = True

    while running:

        socks = dict( work_poller.poll( timeout ) )

        if socks.get( work_receiver ) == zmq.POLLIN:

           # Looks like a message came in on the work_receiver channel.
           # Check if there is enough time left, then run the command.

           work_message = work_receiver.recv_json()

           # Construct the command line.

           task = "%s %s" % ( work_message['cmd'], work_message['file'] )

           walltime = time.time() - starttime
           timeleft = jobtime - walltime

           # Apply the margin of error in the run time.

           if timeleft > ( maxtime * margin ):

              sys.stderr.write( "Worker %s_%d (%d secs left) taking: %s\n"
                                % ( local, wrk_num, timeleft, task ) )

              # Record how long the task takes.

              taskstart = time.time()
              result = shell( task )
              taskend = time.time()
              elapsed = taskend - taskstart
              walltime = taskend - starttime

              if elapsed > maxtime:
                 maxtime = elapsed

              answer_message = {
                 'worker' : "%s_%d" % ( local, wrk_num ),
                 'task' : task,
                 'status' : result[0],
                 'stdout' : result[1],
                 'stderr' : result[2],
                 'tasktime' : elapsed,
                 'walltime' : walltime }
           else:
              sys.stderr.write( "Worker %s_%d (no time left) skipping: %s\n"
                                % ( local, wrk_num, task ) )

              answer_message = {
                 'worker' : "%s_%d" % ( local, wrk_num ),
                 'task' : task,
                 'status' : False,
                 'stdout' : [ 'Insufficient Time', '' ],
                 'stderr' : [ 'Time left: %d; Max Time: %d; Margin: %4.2f' %
                              ( timeleft, maxtime, margin ), '' ],
                 'tasktime' : 0,
                 'walltime' : walltime }

           results_sender.send_json( answer_message )

        # Now get caught up on all control messages.

        chkcontrol = True

        while chkcontrol:

           socks = dict( control_poller.poll( timeout ) )
           
           if socks.get( control_receiver ) == zmq.POLLIN:

              # Looks like a message came in on the control channel.
              # Need to check for either a completion message, or report
              # of maximum time seen.

              control_message = control_receiver.recv()

              if control_message == "FINISHED":

                 # If "FINISHED", shut down the worker.

                 sys.stderr.write( "Worker %s_%d received FINSHED, quitting!\n"
                                   % ( local, wrk_num ) )
                 running = False

              else:

                 # Must be a maximum time report

                 tmp = float( control_message )

                 if tmp > maxtime:
                    maxtime = tmp
                    sys.stderr.write( "Worker %s_%d: maxtime set to %d\n"
                                      % ( local, wrk_num, maxtime ) )
           else:

              # Control channel is empty, so press on.

              chkcontrol = False


def result_manager( rport, cport, tasks ):
    """
    Defines the result manager with gathers up all the results.
    The arguments include:

       rport ... The request port.
       cport ... The control port.
       tasks ... Total number of tasks to expect.

    Results are received as dictionaries from the worker tasks. Obviously,
    the keys must match up on both ends.

    When all tasks are done, the workers are signaled to shut down.
    """

    # Only the host running as dispatcher should be calling this.

    host = ipaddrs( socket.gethostname() )

    # Initialize a zeromq context

    context = zmq.Context()
    
    # Set up a channel to receive results

    results_receiver = context.socket( zmq.PULL )
    results_receiver.bind( "tcp://%s:%s" % ( host, rport ) )

    # Set up a channel to send control commands

    control_sender = context.socket( zmq.PUB )
    control_sender.bind( "tcp://%s:%s" % ( host, cport ) )

    # Set up tracking of maximum time.

    maxtime = 0

    for task_nbr in range( tasks ):
        result_message = results_receiver.recv_json()
        print( "Worker %s ran: %s" % ( result_message['worker'],
                                       result_message['task'] ) )
        print( "Success: %s" % ( result_message['status'] ) )
        print( "Elapsed time: %d" % ( result_message['tasktime'] ))
        print( "Walltime: %d" % ( result_message['walltime'] )) 
        print( "Stdout:" )
        for l in result_message['stdout']:
            if len( l.strip() ) > 0:
                print( "  %s" % ( l.strip() ) )
        print( "Stderr:" )
        for l in result_message['stderr']:
            if len( l.strip() ) > 0:
                print( "  %s" % ( l.strip() ) )
        print( '' )
        if result_message['tasktime'] > maxtime:
           maxtime = result_message['tasktime']
           control_sender.send( "%d"%(maxtime) )

    # Signal to all workers that we are finsihed

    control_sender.send( "FINISHED" )
    time.sleep( 5 )


def Usage():
    global default_jobtime
    print( """
Usage:  python wq.py -h | -d cmd filelist | -w n ms [walltime] 
   where:
      -h .. Display this help message.
   or:
      -d ........ Run as dispatcher and result_manager.
      cmd ....... Absolute path to command (script) to use for task.
                  Will be called with a single file path as argument:
      filelist .. File containing input file names to operate on.
   or:  
      -w ........ Run workers
      n ......... Number of workers (single node).
      ms ........ Host name of mother superior node.
      walltime .. Wallclock time to allow for entire job. May be in
                  the form of ss, mm:ss, hh:mm:ss, or d:hh:mm:ss.
                  (hint: Torque sets PBS_WALLTIME)
""" )
    print( "   The default worker jobtime is hardwired to %d secs - 1 day.\n"
           % ( default_jobtime ) )
    print( "   Revision: $Id: wq.py 69 2014-01-29 20:22:23Z jalupo $\n" )


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

    global default_jobtime

    default_jobtime = 86400
    dport = '5557'
    rport = '5558'
    cport = '5559'

    try:

        opts, args = getopt.getopt( sys.argv[1:], "hdw", [] )

    except getopt.GetoptError, err:

        print str( err )
        Usage()
        sys.exit( 2 )

    for o, a in opts:

        if o == "-d":

            mode = 'd'

        elif o == "-w":

            mode = 'w'

        else:

            Usage()
            sys.exit( 0 )

    if mode == 'w':

	if len( args ) < 2 or len( args ) > 3:

	   Usage()
           sys.exit( 0 )

        # Get number of workers, hostname of mother superior node.

        numw = int( args[0 ] )
	host = ipaddrs( args[1] )

	# Get walltime, if present.

        if len( args ) == 3:

           jobtime = time2secs( args[2] )

        else:

           # Set job time to default time.

           jobtime = default_jobtime

        for wrk_num in range( numw ):

           Process( target = worker,
                    args = ( wrk_num, host, dport, rport,
                             cport, jobtime ) ).start()

    if mode == 'd':

        if len( args ) != 2:
	   Usage()
	   sys.exit( 0 )

        # Get the command to execute as the task, and the list
        # of input files.

        cmd = args[0]
        infile = open( args[1], 'r' )
        files = infile.readlines()
        infile.close()
        tasks = len( files )

        # Fire up the result manager...

        result_manager = Process( target = result_manager,
                                  args = ( rport, cport, tasks ) )
        result_manager.start()

        # Fire up the dispatcher!

        if tasks > 0:
            dispatcher = Process( target = dispatcher,
                                  args = ( dport, cmd, files ) )
            dispatcher.start()
        else:
            Usage()
