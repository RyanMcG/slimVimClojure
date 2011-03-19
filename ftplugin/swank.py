#!/usr/bin/env python)

###############################################################################
#
# SWANK client for Slimv
# swank.py:     SWANK client code for slimv.vim plugin
# Version:      0.8.0
# Last Change:  19 Mar 2011
# Maintainer:   Tamas Kovacs <kovisoft at gmail dot com>
# License:      This file is placed in the public domain.
#               No warranty, express or implied.
#               *** ***   Use At-Your-Own-Risk!   *** ***
# 
############################################################################### 


import sys
import socket
import time
import select
import string

input_port      = 4005
output_port     = 4006
lenbytes        = 6             # Message length is encoded in this number of bytes
maxmessages     = 50            # Maximum number of messages to receive in one listening session
sock            = None          # Swank socket object
id              = 0             # Message id
debug           = False
log             = False         # Set this to True in order to enable logging
logfile         = 'swank.log'   # Logfile name in case logging is on
current_thread  = '0'
debug_activated = False         # Swank debugger activated
read_string     = None          # Thread and tag in Swank read string mode
prompt          = 'SLIMV'       # Command prompt
package         = 'COMMON-LISP-USER' # Current package
actions         = dict()        # Swank actions (like ':write-string'), by message id


###############################################################################
# Basic utility functions
###############################################################################

def logprint(text):
    if log:
        f = open(logfile, "a")
        f.write(text + '\n')
        f.close()

###############################################################################
# Simple Lisp s-expression parser
###############################################################################

# Possible error codes
PARSERR_NOSTARTBRACE        = -1    # s-expression does not start with a '('
PARSERR_NOCLOSEBRACE        = -2    # s-expression does not end with a '('
PARSERR_NOCLOSESTRING       = -3    # string is not closed with double quote
PARSERR_MISSINGLITERAL      = -4    # literal is missing after the escape character
PARSERR_EMPTY               = -5    # s-expression is empty


def parse_comment( sexpr ):
    """Parses a ';' Lisp comment till the end of line, returns comment length
    """
    pos = sexpr.find( '\n' )
    if pos >= 0:
        return pos + 1
    return len( sexpr )

def parse_keyword( sexpr ):
    """Parses a Lisp keyword, returns keyword length
    """
    for pos in range( len( sexpr ) ):
        if sexpr[pos] in string.whitespace + ')]':
            return pos
    return pos

def parse_sub_sexpr( sexpr, opening, closing ):
    """Parses a Lisp sub -expression, returns parsed string length
       and a Python list built from the s-expression,
       expression can be a Clojure style list surrounded by braces
    """
    result = []
    l = len( sexpr )
    for pos in range( l ):
        # Find first opening '(' or '['
        if sexpr[pos] == opening:
            break
        if not sexpr[pos] in string.whitespace:
            # S-expression does not start with '(' or '['
            return [PARSERR_NOSTARTBRACE, result]
    else:
        # Empty s-expression
        return [PARSERR_EMPTY, result]

    pos = pos + 1
    quote_cnt = 0
    while pos < l:
        literal = 0
        if sexpr[pos] == '\\':
            literal = 1
            pos = pos + 1
            if pos == l:
                return [PARSERR_MISSINGLITERAL, result]
        if not literal and sexpr[pos] == '"':
            # We toggle a string
            quote_cnt = 1 - quote_cnt
            if quote_cnt == 1:
                quote_pos = pos
            else:
                result = result + [sexpr[quote_pos:pos+1]]
        elif quote_cnt == 0:
            # We are not in a string
            if not literal and sexpr[pos] == '(':
                # Parse sub expression
                [slen, subresult] = parse_sub_sexpr( sexpr[pos:], '(', ')' )
                if slen < 0:
                    # Sub expression parsing error
                    return [slen, result]
                result = result + [subresult]
                pos = pos + slen - 1
            elif not literal and sexpr[pos] == '[':
                # Parse sub expression
                [slen, subresult] = parse_sub_sexpr( sexpr[pos:], '[', ']' )
                if slen < 0:
                    # Sub expression parsing error
                    return [slen, result]
                result = result + [subresult]
                pos = pos + slen - 1
            elif not literal and sexpr[pos] == closing:
                # End of this sub expression
                return [pos + 1, result]
            elif not literal and sexpr[pos] != closing and sexpr[pos] in ')]':
                # Wrong closing brace/bracket
                return [PARSERR_NOCLOSEBRACE, result]
            elif not literal and sexpr[pos] == ';':
                # Skip coment
                pos = pos + parse_comment( sexpr[pos:] ) - 1
            elif not sexpr[pos] in string.whitespace + '\\':
                # Parse keyword
                klen = parse_keyword( sexpr[pos:] )
                result = result + [sexpr[pos:pos+klen]]
                pos = pos + klen - 1
        pos = pos + 1

    if quote_cnt != 0:
        # Last string is not closed
        return [PARSERR_NOCLOSESTRING, result]
    # Closing ')' or ']' not found
    return [PARSERR_NOCLOSEBRACE, result]

def parse_sexpr( sexpr ):
    """Parses a Lisp s-expression, returns parsed string length
       and a Python list built from the s-expression
    """
    return parse_sub_sexpr( sexpr, '(', ')' )


###############################################################################
# Swank server interface
###############################################################################

class swank_action:
    def __init__ (self, id, name):
        self.id = id
        self.name = name
        self.result = ''
        self.pending = True

def unquote(s):
    if len(s) < 2:
        return s
    if s[0] == '"' and s[-1] == '"':
        return s[1:-1].replace('\\"', '"')
    else:
        return s

def requote(s):
    return '"' + s.replace('"', '\\"') + '"'

def make_keys(lst):
    keys = {}
    for i in range(len(lst)):
        if i < len(lst)-1 and lst[i][0] == ':':
            keys[lst[i]] = unquote( lst[i+1] )
    return keys

def parse_plist(lst, keyword):
    for i in range(0, len(lst), 2):
        if keyword == lst[i]:
            return unquote(lst[i+1])
    return ''

def swank_send(text):
    global sock

    logprint('[---Sent---]\n' + text)
    l = hex(len(text))[2:]
    t = '0'*(lenbytes-len(l)) + l + text
    if debug:
        print 'Sending:', t
    try:
        sock.send(t)
    except socket.error:
        sys.stdout.write( 'Socket error when sending to SWANK server.\n' )
	swank_disconnect()

def swank_recv(msglen):
    global sock

    rec = ''
    if msglen > 0:
        sock.setblocking(0)
        ready = select.select([sock], [], [], 0.1) # 0.1: timeout in seconds
        if ready[0]:
            l = msglen
            sock.setblocking(1)
            data = sock.recv(l)
            while data and len(rec) < msglen:
                rec = rec + data
                l = l - len(data)
                if l > 0:
                    data = sock.recv(l)
    return rec

def swank_parse_inspect(struct):
    buf = '\n \nInspecting ' + parse_plist(struct, ':title') + '\n--------------------'
    pcont = parse_plist(struct, ':content')
    cont = pcont[0]
    lst = []
    desc = ''
    sep = ''
    for el in cont:
        if type(el) == list:
            lst.append([desc, sep, unquote(el[1]), unquote(el[2])])
            desc = ''
            sep = ''
        else:
            stg = unquote(el)
            if stg == "\n":
                if desc:
                    lst.append([desc, sep, '', ''])
                desc = ''
                sep = ''
            elif stg == ': ' or stg == ' ':
                sep = unquote(stg)
            else:
                desc = unquote(stg)
    for (desc, sep, data, item) in lst:
        buf = buf + "\n"
        if item:
            buf = buf + "[" + item + "]  "
        buf = buf + "%s%s%s" % (desc, sep, data)
    buf = buf + '\n \n[<<]'
    return buf

def swank_listen():
    global output_port
    global debug_activated
    global read_string
    global current_thread
    global prompt
    global package

    retval = ''
    msgcount = 0
    while msgcount < maxmessages:
        rec = swank_recv(lenbytes)
        if rec == '':
            break
        msgcount = msgcount + 1
        if debug:
            print 'swank_recv received', rec
        msglen = int(rec, 16)
        if debug:
            print 'Received length:', msglen
        if msglen > 0:
            rec = swank_recv(msglen)
            logprint('[-Received-]\n' + rec)
            [s, r] = parse_sexpr( rec )
            if debug:
                print 'Parsed:', r
            if len(r) > 0:
                r_id = r[-1]
                message = r[0].lower()
                if debug:
                    print 'Message:', message

                if message == ':open-dedicated-output-stream':
                    output_port = int( r[1].lower(), 10 )
                    if debug:
                        print ':open-dedicated-output-stream result:', output_port
                    break

                elif message == ':write-string':
                    # REPL has new output to display
                    s = unquote(r[1])
                    retval = retval + s

                elif message == ':read-string':
                    # RERL requests entering a string
                    read_string = r[1:3]

                elif message == ':new-package':
                    package = unquote( r[1] )
                    prompt  = unquote( r[2] )

                elif message == ':return':
                    read_string = None
                    result = r[1][0].lower()
                    if type(r_id) == str and r_id in actions:
                        action = actions[r_id]
                        action.pending = False
                    else:
                        action = None
                    if log:
                        logprint('[Actionlist]')
                        for k,a in sorted(actions.items()):
                            if a.pending:
                                pending = 'pending '
                            else:
                                pending = 'finished'
                            logprint("%s: %s %s %s" % (k, str(pending), a.name, a.result))

                    if result == ':ok':
                        params = r[1][1]
                        if type(params) == str:
                            element = params.lower()
                            if element == 'nil':
                                # No more output from REPL, write new prompt
                                if len(retval) > 0 and retval[-1] != '\n':
                                    retval = retval + '\n'
                                retval = retval + prompt + '> '
                            else:
                                s = unquote(params)
                                retval = retval + s
                                if action:
                                    action.result = retval
                        
                        elif type(params) == list:
                            if type(params[0]) == list: 
                                params = params[0]
                            element = params[0].lower()
                            if element == ':present':
                                # No more output from REPL, write new prompt
                                retval = retval + unquote(params[1][0][0]) + '\n' + prompt + '> '
                            elif element == ':values':
                                retval = retval + params[1][0] + '\n'
                            elif element == ':suppress-output':
                                pass
                            elif element == ':pid':
                                conn_info = make_keys(params)
                                pid = conn_info[':pid']
                                ver = conn_info[':version']
                                imp = make_keys( conn_info[':lisp-implementation'] )
                                pkg = make_keys( conn_info[':package'] )
                                package = pkg[':name']
                                prompt = pkg[':prompt']
                                vim.command('let s:swank_version="' + ver + '"')
                                retval = retval + imp[':type'] + '  Port: ' + str(input_port) + '  Pid: ' + pid + '\n; SWANK ' + ver
                                logprint(' Package:' + package + ' Prompt:' + prompt)
                            elif element == ':name':
                                keys = make_keys(params)
                                retval = retval + '  ' + keys[':name'] + ' = ' + keys[':value'] + '\n'
                            elif element == ':title':
                                retval = swank_parse_inspect(params)
                            else:
                                logprint(str(element))
                    elif result == ':abort':
                        debug_activated = False
                        vim.command('let s:debug_activated=0')
                        if len(r[1]) > 1:
                            retval = retval + '; Evaluation aborted on ' + unquote(r[1][1]) + '\n' + prompt + '> '
                        else:
                            retval = retval + '; Evaluation aborted\n' + prompt + '> '

                elif message == ':inspect':
                    retval = swank_parse_inspect(r[1])

                elif message == ':debug':
                    [thread, level, condition, restarts, frames, conts] = r[1:7]
                    retval = retval + '\n' + unquote(condition[0]) + '\n' + unquote(condition[1]) + '\n\nRestarts:\n'
                    for i in range( len(restarts) ):
                        r0 = unquote( restarts[i][0] )
                        r1 = unquote( restarts[i][1] )
                        retval = retval + str(i).rjust(3) + ': [' + r0 + '] ' + r1 + '\n'
                    retval = retval + '\nBacktrace:\n'
                    for f in frames:
                        frame = str(f[0])
                        ftext = unquote( f[1] )
                        ftext = ftext.replace('\n', '')
                        ftext = ftext.replace('\\\\n', '')
                        retval = retval + frame.rjust(3) + ': ' + ftext + '\n'
                    retval = retval + prompt + '> '

                elif message == ':debug-activate':
                    debug_activated = True
                    vim.command('let s:debug_activated=1')
                    current_thread = r[1]

                elif message == ':debug-return':
                    debug_activated = False
                    vim.command('let s:debug_activated=0')
                    retval = retval + '; Quit to level ' + r[2] + '\n' + prompt + '> '

                elif message == ':ping':
                    [thread, tag] = r[1:3]
                    swank_send('(:emacs-pong ' + thread + ' ' + tag + ')')
    return retval

def swank_rex(action, cmd, package, thread):
    global id
    id = id + 1
    key = str(id)
    actions[key] = swank_action(key, action)
    form = '(:emacs-rex ' + cmd + ' ' + package + ' ' + thread + ' ' + str(id) + ')\n'
    swank_send(form)

def swank_connection_info():
    swank_rex(':connection-info', '(swank:connection-info)', 'nil', 't')

def swank_create_repl():
    swank_rex(':create-repl', '(swank:create-repl nil)', 'nil', 't')

def swank_eval(exp, package):
    cmd = '(swank:listener-eval ' + requote(exp) + ')'
    swank_rex(':listener-eval', cmd, '"'+package+'"', ':repl-thread')

def swank_pprint_eval(exp, package):
    cmd = '(swank:pprint-eval ' + requote(exp) + ')'
    swank_rex(':pprint-eval', cmd, '"'+package+'"', ':repl-thread')

def swank_interrupt():
    swank_send('(:emacs-interrupt :repl-thread)')

def swank_invoke_restart(level, restart):
    cmd = '(swank:invoke-nth-restart-for-emacs ' + level + ' ' + restart + ')'
    swank_rex(':invoke-nth-restart-for-emacs', cmd, 'nil', current_thread)

def swank_throw_toplevel():
    swank_rex(':throw-to-toplevel', '(swank:throw-to-toplevel)', 'nil', current_thread)

def swank_invoke_abort():
    swank_rex(':sldb-abort', '(swank:sldb-abort)', 'nil', current_thread)

def swank_invoke_continue():
    swank_rex(':sldb-continue', '(swank:sldb-continue)', 'nil', current_thread)

def swank_frame_locals(frame):
    cmd = '(swank:frame-locals-for-emacs ' + frame + ')'
    swank_rex(':frame-locals-for-emacs', cmd, 'nil', current_thread)
    sys.stdout.write( 'Locals:\n' )

def swank_describe_symbol(fn):
    cmd = '(swank:describe-symbol "' + fn + '")'
    swank_rex(':describe-symbol', cmd, 'nil', 't')

def swank_describe_function(fn):
    cmd = '(swank:describe-function "' + fn + '")'
    swank_rex(':describe-function', cmd, 'nil', 't')

def swank_op_arglist(op):
    cmd = '(swank:operator-arglist "' + op + '" "' + package + '")'
    swank_rex(':operator-arglist', cmd, 'nil', 't')

def swank_return_string(s):
    swank_send('(:emacs-return-string ' + read_string[0] + ' ' + read_string[1] + ' ' + s + ')')

def swank_inspect(symbol):
    cmd = '(swank:init-inspector "' + symbol + '")'
    swank_rex(':init-inspector', cmd, 'nil', 't')
    #if symbol.find('::') < 0:
    #    symbol = package + '::' + symbol
    ##symbol = symbol.replace("'", "\\'")
    #cmd = '(swank:inspect-in-emacs ' + symbol + ')'
    #swank_rex(':inspect-in-emacs', cmd, 'nil', 't')

def swank_inspect_nth_part(n):
    cmd = '(swank:inspect-nth-part ' + str(n) + ')'
    swank_rex(':inspect-nth-part', cmd, 'nil', 't')

def swank_inspector_pop():
    swank_rex(':inspector-pop', '(swank:inspector-pop)', 'nil', 't')

def swank_toggle_trace(symbol):
    cmd = '(swank:swank-toggle-trace "' + symbol + '")'
    swank_rex(':swank-toggle-trace', cmd, 'nil', 't')

def swank_untrace_all():
    swank_rex(':untrace-all', '(swank:untrace-all)', 'nil', 't')

def swank_connect(portvar, resultvar):
    """Create socket to swank server and request connection info
    """
    global sock
    global input_port

    if not sock:
        try:
            input_port = int(vim.eval(portvar))
            swank_server = ('localhost', input_port)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(swank_server)
            swank_connection_info()
            vim.command('let ' + resultvar + '=""')
            return sock
        except socket.error:
            vim.command('let ' + resultvar + '="SWANK server is not running."')
            sock = None
            return sock
    vim.command('let ' + resultvar + '=""')
    return sock

def swank_disconnect():
    global sock
    try:
        # Try to close socket but don't care if doesn't succeed
        sock.close()
    finally:
        sock = None
        vim.command('let s:swank_connected = 0')
        sys.stdout.write( 'Connection to SWANK server is closed.\n' )

def swank_input(formvar, packagevar):
    form = vim.eval(formvar)
    if read_string:
        # We are in :read-string mode, pass string entered to REPL
        swank_return_string('"' + form + '\n"')
    elif debug_activated and form[0] != '(' and form[0] != ' ':
        # We are in debug mode and an SLDB command follows (that is not an s-expr)
        if form[0] == '#':
            swank_frame_locals(form[1:])
        elif form[0].lower() == 'q':
            swank_throw_toplevel()
        elif form[0].lower() == 'a':
            swank_invoke_abort()
        elif form[0].lower() == 'c':
            swank_invoke_continue()
        else:
            swank_invoke_restart("1", form)
    elif form[0] == '[':
        if form[1] == '-':
            swank_inspector_pop()
        else:
            swank_inspect_nth_part(form[1:-2])
    else:
        # Normal s-expression evaluation
        pkg = vim.eval(packagevar)
        if pkg == '':
            pkg = package
        swank_eval(form, pkg)

def swank_output():
    global sock

    if not sock:
        return "SWANK server is not connected."
    result = swank_listen()
    sys.stdout.write(result)
    return result

def swank_response(name):
    for k,a in sorted(actions.items()):
        if not a.pending and (name == '' or name == a.name):
            vc = ":let s:swank_action='" + a.name + "'"
            vim.command(vc)
            sys.stdout.write(a.result)
            actions.pop(a.id)
            vc = ":let s:swank_actions_pending=" + str(len(actions))
            vim.command(vc)
            return
    vc = ":let s:swank_action=''"
    vim.command(vc)
    vc = ":let s:swank_actions_pending=" + str(len(actions))
    vim.command(vc)

