#!/usr/bin/env python

###############################################################################
#
# Client/Server code for Slimv
# slimv.py:     Client/Server code for slimv.vim plugin
# Version:      0.1.4
# Last Change:  21 Feb 2009
# Maintainer:   Tamas Kovacs <kovisoft at gmail dot com>
# License:      This file is placed in the public domain.
#               No warranty, express or implied.
#               *** ***   Use At-Your-Own-Risk!   *** ***
# 
###############################################################################

import os
import sys
import getopt
import time
import shlex
import socket
from subprocess import Popen, PIPE, STDOUT
from threading import Thread, BoundedSemaphore

autoconnect = 1             # Start and connect server automatically

HOST        = ''            # Symbolic name meaning the local host
PORT        = 5151          # Arbitrary non-privileged port

debug_level = 0             # Debug level for diagnostic messages
terminate   = 0             # Main program termination flag

python_path = 'python'      # Path of the Python interpreter (overridden via command line args)
lisp_path   = 'clisp.exe'   # Path of the Lisp interpreter (overridden via command line args)
slimv_path  = 'slimv.py'    # Path of this script (determined later)
run_cmd     = ''            # Complex server-run command (if given via command line args)

newline     = '\n'

# Are we running on Windows (otherwise assume Linux, sorry for other OS-es)
mswindows = (sys.platform == 'win32')


def log( s, level ):
    """Print diagnostic messages according to the actual debug level.
    """
    if debug_level >= level:
        print s


###############################################################################
#
# Client part
#
###############################################################################

def start_server( filename ):
    """Spawn server. Does not check if the server is already running.
    """
    if run_cmd == '':
        # Complex run command not given, build it from the information available
        if mswindows:
            cmd = []
        else:
            cmd = ['xterm', '-T', 'Slimv', '-e']
        cmd = cmd + [python_path, slimv_path, '-p', str(PORT), '-l', lisp_path, '-s']
        if filename != '':
            cmd = cmd + ['-o', filename]
    else:
        cmd = shlex.split(run_cmd)

    # Start server
    #TODO: put in try-block
    if mswindows:
        CREATE_NEW_CONSOLE = 16
        server = Popen( cmd, creationflags=CREATE_NEW_CONSOLE )
    else:
        server = Popen( cmd )

    # Allow subprocess (server) to start
    time.sleep( 2.0 )


def connect_server( output_filename ):
    """Try to connect server, if server not found then spawn it.
       Return socket object on success, None on failure.
    """

    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    try:
        s.connect( ( 'localhost', PORT ) )
    except socket.error, msg:
        if autoconnect:
            # We need to try to start the server automatically
            s.close()
            start_server( output_filename )

            # Open socket to the server
            s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            try:
                s.connect( ( 'localhost', PORT ) )
            except socket.error, msg:
                s.close()
                s =  None
        else:   # not autoconnect
            print "Server not found"
            s = None
    return s


def send_line( server, line ):
    """Send a line to the server:
       first send line length in 4 bytes, then send the line itself.
    """
    l = len(line)
    lstr = chr(l&255) + chr((l>>8)&255) + chr((l>>16)&255) + chr((l>>24)&255)
    server.send( lstr )     # send message length first
    server.send( line )     # then the message itself

    time.sleep(0.01)        # give a little chance to receive some output from the REPL before the next query
                            #TODO: synchronize it correctly


def client_file( input_filename, output_filename ):
    """Main client routine - input file version:
       starts server if needed then send text to server.
       Input is read from input file.
    """
    s = connect_server( output_filename )
    if s is None:
        return

    try:
        file = open( input_filename, 'rt' )
        try:
            # Send contents of the file to the server
            for line in file:
                send_line( s, line.rstrip( '\n' ) )
        finally:
            file.close()
    except:
        return

    s.close()


###############################################################################
#
# Server part
#
###############################################################################

class repl_buffer:
    def __init__ ( self, output_pipe, output_filename ):

        self.output   = output_pipe
        self.filename = output_filename
        self.sema     = BoundedSemaphore()
                            # Semaphore to synchronize access to the global display queue

    def write( self, text, fileonly=False ):
        """Write text into the global display queue buffer.
        """
        self.sema.acquire()
        if not fileonly:
            try:
                # Write all lines to the display
                os.write( self.output.fileno(), text )
            except:
                pass

        if output_filename != '':
            tries = 4
            while tries > 0:
                try:
                    file = open( output_filename, 'at' )
                    try:
                        #file.write( text )
                        os.write(file.fileno(), text )
                    finally:
                        file.close()
                    tries = 0
                except:
                    tries = tries - 1
        self.sema.release()


class socket_listener( Thread ):
    """Server thread to receive text from the client via socket.
    """

    def __init__ ( self, inp, buffer ):
        Thread.__init__( self )
        self.inp = inp
        self.buffer = buffer

    def run( self ):
        global terminate

        # Open server socket
        self.s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.s.bind( (HOST, PORT) )

        while not terminate:
            # Listen server socket
            self.s.listen( 1 )
            conn, addr = self.s.accept()

            while not terminate:
                l = 0
                lstr = ''
                # Read length first, it comes in 4 bytes
                try:
                    lstr = conn.recv(4)
                    if len( lstr ) <= 0:
                        break
                except:
                    break
                if terminate:
                    break
                l = ord(lstr[0]) + (ord(lstr[1])<<8) + (ord(lstr[2])<<16) + (ord(lstr[3])<<24)
                if l > 0:
                    # Valid length received, now wait for the message
                    try:
                        # Read the message itself
                        received = conn.recv(l)
                        if len( received ) < l:
                            break
                    except:
                        break

                    if received[0:16] == 'SLIMV::INTERRUPT':
                        if mswindows:
                            import win32api
                            CTRL_C_EVENT = 0
                            win32api.GenerateConsoleCtrlEvent( CTRL_C_EVENT, 0 )
                    else:
                        # Fork here: write message to the stdin of REPL
                        # and also write it to the display (display queue buffer)
                        self.inp.write   ( received + newline )
                        self.buffer.write( received + newline )

            conn.close()


class output_listener( Thread ):
    """Server thread to receive REPL output.
    """

    def __init__ ( self, out, buffer ):
        Thread.__init__( self )
        self.out = out
        self.buffer = buffer

    def run( self ):
        global terminate

        while not terminate:
            try:
                # Read input from the stdout of REPL
                # and write it to the display (display queue buffer)
                if mswindows:
                    c = self.out.read( 1 )
                    if ord( c ) == 0x0D:
                        # Special handling of 0x0D+0x0A on Windows
                        c2 = self.out.read( 1 )
                        if ord( c2 ) == 0x0A:
                            self.buffer.write( '\n' )
                        else:
                            self.buffer.write( c )
                            self.buffer.write( c2 )
                    else:
                        self.buffer.write( c )
                else:
                    # On Linux set read mode to non blocking
                    import fcntl, select
                    flag = fcntl.fcntl(self.out.fileno(), fcntl.F_GETFL)
                    fcntl.fcntl(self.out.fileno(), fcntl.F_SETFL, flag | os.O_NONBLOCK)

                    r = select.select([self.out.fileno()], [], [], 0)[0]
                    if r:
                        c = os.read( self.out.fileno(), 1 )
                        self.buffer.write( c )
            except:
                break


def server( output_filename ):
    """Main server routine: starts REPL and helper threads for
       sending and receiving data to/from REPL.
    """
    global terminate

    # First check if server already runs
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    try:
        s.connect( ( 'localhost', PORT ) )
    except socket.error, msg:
        # Server not found, our time has come, we'll start a new server in a moment
        pass
    else:
        # Server found, nothing to do here
        s.close()
        print "Server is already running"
        return

    # Build Lisp-starter command
    cmd = shlex.split( lisp_path.replace( '\\', '\\\\' ) )

    # Start Lisp
    repl = Popen( cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT )

    buffer = repl_buffer( sys.stdout, output_filename )

    # Create and start helper threads
    sl = socket_listener( repl.stdin, buffer )
    sl.start()
    ol = output_listener( repl.stdout, buffer )
    ol.start()

    # Allow Lisp to start, confuse it with some fancy Slimv messages
    sys.stdout.write( ";;; Slimv server is started on port " + str(PORT) + newline )
    sys.stdout.write( ";;; Slimv is spawning REPL..." + newline )
    time.sleep(0.5)             # wait for Lisp to start
    sys.stdout.write( ";;; Slimv connection established" + newline )

    # Main server loop
    while not terminate:
        try:
            # Read input from the console and write it
            # to the stdin of REPL
            text = raw_input()
            repl.stdin.write( text + newline )
            buffer.write( text + newline, True )
        except EOFError:
            # EOF (Ctrl+Z on Windows, Ctrl+D on Linux) pressed?
            terminate = 1
        except KeyboardInterrupt:
            # Interrupted from keyboard (Ctrl+C)?
            # We just ignore it here, it will be propagated to the child anyway
            pass

    # The socket is opened here only for waking up the server thread
    # in order to recognize the termination message
    #TODO: exit REPL if this script is about to exit
    cs = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    try:
        cs.connect( ( 'localhost', PORT ) )
        cs.send( " " )
    finally:
        # We don't care if this above fails, we'll exit anyway
        cs.close()

    # Send exit command to child process and
    # wake output listener up at the same time
    try:
        repl.stdin.close()
    except:
        # We don't care if this above fails, we'll exit anyway
        pass

    # Be nice
    print 'Thank you for using Slimv.'

    # Wait for the child process to exit
    time.sleep(1)


def escape_path( path ):
    """Surround path containing spaces with backslash + double quote,
       so that it can be passed as a command line argument.
    """
    if path.find( ' ' ) < 0:
        return path
    if path[0:2] == '\\\"':
        return path
    elif path[0] == '\"':
        return '\\' + path + '\\'
    else:
        return '\\\"' + path + '\\\"'


def usage():
    """Displays program usage information.
    """
    progname = os.path.basename( sys.argv[0] )
    print 'Usage: ', progname + ' [-d LEVEL] [-s] [-o OUTFILE] [-f INFILE]'
    print
    print 'Options:'
    print '  -?, -h, --help                show this help message and exit'
    print '  -l PATH, --lisp=PATH          path of Lisp interpreter'
    print '  -r PATH, --run=PATH           full command to run the server'
    print '  -p PORT, --port=PORT          port number to use by the server/client'
    print '  -d LEVEL, --debug=LEVEL       set debug LEVEL (0..3)'
    print '  -s                            start server'
    print '  -o OUTFILE                    write REPL output to OUTFILE'
    print '  -f INFILE, --file=INFILE      start client and send contents of file'
    print '                                named INFILE to server'


###############################################################################
#
# Main program
#
###############################################################################

if __name__ == '__main__':

    EXIT, SERVER, CLIENT = range( 3 )
    mode = EXIT
    slimv_path = sys.argv[0]
    python_path = sys.executable
    input_filename = ''
    output_filename = ''

    # Always this trouble with the path/filenames containing spaces:
    # enclose them in double quotes
    if python_path.find( ' ' ) >= 0:
        python_path = '"' + python_path + '"'

    # Get command line options
    try:
        opts, args = getopt.getopt( sys.argv[1:], '?hcso:f:p:l:r:d:', \
                                    ['help', 'client', 'server', 'output=', 'file=', 'port=', 'lisp=', 'run=', 'debug='] )

        # Process options
        for o, a in opts:
            if o in ('-?', '-h', '--help'):
                usage()
                break
            if o in ('-p', '--port'):
                try:
                    PORT = int(a)
                except:
                    # If given port number is malformed, then keep default value
                    pass
            if o in ('-l', '--lisp'):
                lisp_path = a
            if o in ('-r', '--run'):
                run_cmd = a
            if o in ('-d', '--debug'):
                try:
                    debug_level = int(a)
                except:
                    # If given level is malformed, then keep default value
                    pass
            if o in ('-s', '--server'):
                mode = SERVER
            if o in ('-o', '--output'):
                output_filename = a
            if o in ('-c', '--client'):
                mode = CLIENT
            if o in ('-f', '--file'):
                mode = CLIENT
                input_filename = a

    except getopt.GetoptError:
        # print help information and exit:
        usage()

    if mode == SERVER:
        # We are started in server mode
        server( output_filename )

    if mode == CLIENT:
        # We are started in client mode
        if run_cmd != '':
            # It is possible to pass special argument placeholders to run_cmd
            run_cmd = run_cmd.replace( '@p', escape_path( python_path ) )
            run_cmd = run_cmd.replace( '@s', escape_path( slimv_path ) )
            run_cmd = run_cmd.replace( '@l', escape_path( lisp_path ) )
            run_cmd = run_cmd.replace( '@o', escape_path( output_filename ) )
            run_cmd = run_cmd.replace( '@@', '@' )
            log( run_cmd, 1 )
        if input_filename != '':
            client_file( input_filename, output_filename )
        else:
            start_server( output_filename )

# --- END OF FILE ---
