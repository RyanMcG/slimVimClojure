" slimv.vim:    The Superior Lisp Interaction Mode for VIM
" Last Change:	2008 Mar 26
" Maintainer:	Tamas Kovacs <kovisoft@gmail.com>
" License:	This file is placed in the public domain.
"               No warranty, express or implied.
"               *** ***   Use At-Your-Own-Risk!   *** ***
"
" =====================================================================
"
"  TODO: make it work on Linux
"  TODO: is it possible to redirect output to VIM buffer?
"  TODO: compile related functions and keybindings
"  TODO: documentation commands
"  TODO: possibility to use cmd frontend (like Console: console "/k <command>")
"  TODO: autodetect Python and Lisp installation directory
" You should look at (HKEY_LOCAL_MACHINE,HKEY_CURRENT_USER)/Software/Python. 
"
" =====================================================================
"  Load Once:
if &cp || exists("g:slimv_loaded")
    finish
endif

let g:slimv_loaded        = 1
let g:slimv_loaded_python = 0

if has("win32") || has("win95") || has("win64") || has("win16")
    let g:slimv_windows   = 1
else
    let g:slimv_windows   = 0
endif

" =====================================================================
"  Global variable definitions
" =====================================================================

if !exists('g:slimv_port')
    "TODO: pass this to the client
    let g:slimv_port = 5151
endif

function! SlimvAutodetectPython()
    if executable( 'python' )
	return 'python'
    endif

    if g:slimv_windows
	" Try to find Python on the standard installation places
	let pythons = split( globpath( 'c:/python*,c:/Program Files/python*', 'python.exe' ), '\n' )
	if len( pythons ) > 0
	    return pythons[0]
	endif
	" Go deeper in subdirectories
	let pythons = split( globpath( 'c:/python*/**,c:/Program Files/python*/**', 'python.exe' ), '\n' )
	if len( pythons ) > 0
	    return pythons[0]
	endif
	return ''
    else
	return ''
    endif
endfunction

function! SlimvAutodetectLisp()
    if executable( 'clisp' )
	" Common Lisp
	return 'clisp'
    endif
    if executable( 'gcl' )
	" GNU Common Lisp
	return 'gcl'
    endif
    if executable( 'cmucl' )
	" Carnegie Mellon University Common Lisp
	return 'cmucl'
    endif
    if executable( 'sbcl' )
	" Steel Bank Common Lisp
	return 'sbcl'
    endif
    if executable( 'ecl' )
	" Embeddable Common Lisp
	return 'ecl'
    endif
    if executable( 'acl' )
	" Allegro Common Lisp
	return 'acl'
    endif
    if executable( 'lwl' )
	" LispWorks
	return 'lwl'
    endif

    if g:slimv_windows
	"return 'c:/lispbox/clisp-2.37/clisp.exe'
	" Try to find Python on the standard installation places
	let lisps = split( globpath( 'c:/*lisp*,c:/Program Files/*lisp*', '*lisp.exe' ), '\n' )
	if len( lisps ) > 0
	    return lisps[0]
	endif
	let lisps = split( globpath( 'c:/*lisp*/*,c:/Program Files/*lisp*/*', '*lisp.exe' ), '\n' )
	if len( lisps ) > 0
	    return lisps[0]
	endif
	let lisps = split( globpath( 'c:/*lisp*/**,c:/Program Files/*lisp*/**', '*lisp.exe' ), '\n' )
	if len( lisps ) > 0
	    return lisps[0]
	endif
	let lisps = split( globpath( 'c:/gcl*,c:/Program Files/gcl*', 'gcl.exe' ), '\n' )
	if len( lisps ) > 0
	    return lisps[0]
	endif
	let lisps = split( globpath( 'c:/cmucl*,c:/Program Files/cmucl*', 'cmucl.exe' ), '\n' )
	if len( lisps ) > 0
	    return lisps[0]
	endif
	let lisps = split( globpath( 'c:/sbcl*,c:/Program Files/sbcl*', 'sbcl.exe' ), '\n' )
	if len( lisps ) > 0
	    return lisps[0]
	endif
	let lisps = split( globpath( 'c:/ecl*,c:/Program Files/ecl*', 'ecl.exe' ), '\n' )
	if len( lisps ) > 0
	    return lisps[0]
	endif
	"return 'clisp.exe'
	"return 'c:/lispbox/clisp-2.37/clisp.exe'
	"return '\"c:/lispbox/clisp-2.37/clisp.exe -ansi\"'
	"TODO: remove this hack
	"return '"c:/lispbox/clisp-2.37/clisp.exe -ansi"'
	return ''
    else
	return ''
    endif
endfunction

function! SlimvClientCommand()
    if g:slimv_python == '' || g:slimv_lisp == ''
	" We don't have enough information to build the command to start the client
	return ''
    endif
    if g:slimv_port == 5151
	let port = ''
    else
	" Using port number other than default, must pass it to client
	let port = ' -p ' . g:slimv_port
    endif
    if g:slimv_windows
	"return g:slimv_python . ' "' . g:slimv_path . '"' . port  . ' -l ' . g:slimv_lisp
"	return g:slimv_python . ' "' . g:slimv_path . '"' . port . ' -r ' .
"	       \ '"console -w Slimv -r \"/k @p @s -l @l -s\""' . ' -l ' . g:slimv_lisp
	return g:slimv_python . ' "' . g:slimv_path . '"' . port . ' -r ' .
	       \ '"console -w Slimv -r \"/k @p @s -l ' . g:slimv_lisp . ' -s\""'
    else
	return g:slimv_python . ' ' . g:slimv_path . port . ' -l ' . g:slimv_lisp
    endif
endfunction

if !exists('g:slimv_path')
"    if g:slimv_windows
"	"let g:slimv_path = $VIMRUNTIME . "/plugin/slimv.py"
"	let g:slimv_path = $VIM . '/vimfiles/plugin/slimv.py'
"    else
"	let g:slimv_path = $HOME . '/.vim/plugin/slimv.py'
"    endif
    "let g:slimv_path = globpath(&runtimepath, '**/slimv.py')
    "let g:slimv_path = globpath(&runtimepath, '*/slimv.py')
    let plugins = split( globpath( &runtimepath, 'plugin/**/slimv.py'), '\n' )
    if len( plugins ) > 0
	let g:slimv_path = plugins[0]
    else
	let g:slimv_path = 'slimv.py'
    endif
endif

if !exists('g:slimv_python')
    let g:slimv_python = SlimvAutodetectPython()
endif

if !exists('g:slimv_lisp')
    let g:slimv_lisp = SlimvAutodetectLisp()
endif

"if !exists('g:slimv_server')
"    if g:slimv_windows
"	let g:slimv_command = g:slimv_python . ' \"' . g:slimv_path . '\"'
"	"let g:slimv_server = 'console -r "/k ' . g:slimv_python . ' \"' . g:slimv_path . '\" -l ' . g:slimv_lisp . ' -s"'
"	let g:slimv_server = ':!start console -r "/k ' . g:slimv_python . ' \"' . g:slimv_path . '\" -l ' . g:slimv_lisp . ' -s"'
"	"let g:slimv_server = 'console -r "/k c:/python24/python.exe \"c:/Program Files/Vim/vimfiles/plugin/slimv.py\" -l \"c:/lispbox/clisp-2.37/clisp.exe -ansi\" -s"'
"	"let g:slimv_server = g:slimv_python . ' "' . g:slimv_path . '" -l ' . g:slimv_lisp . ' -s'
"    else
"	let g:slimv_server = ':!xterm -e ' . g:slimv_python . ' ' . g:slimv_path . ' -l ' . g:slimv_lisp . ' -s &'
"    endif
"endif

if !exists('g:slimv_client')
    let g:slimv_client = SlimvClientCommand()
    "let g:slimv_client = ''
endif


"let g:term = 'console -r \"/k %p \\"%s\\" -l %l -s\"'
"let g:term1 = substitute( g:term,  '%p', g:slimv_python, 'g' )
"let g:term2 = substitute( g:term1, '%s', g:slimv_path, 'g' )
"let g:term3 = substitute( g:term2, '%l', g:slimv_lisp, 'g' )
"let g:client = '%p %s -r \"console -r \\"/k %p \\\"%s\\\" -l %l -s\\"\" -c'
"let g:client = '%p %s -r \"%p \\"%s\\" -l %l -s\" -c'


" ---------------------------------------------------------------------

"TODO: change %1 to @1 to be conform with @p, @s, @l above (or just leave it alone?)
if !exists("g:slimv_template_pprint")
    let g:slimv_template_pprint = '(dolist (o %1)(pprint o))'
endif

if !exists("g:slimv_template_undefine")
    let g:slimv_template_undefine = '(fmakunbound (read-from-string "%1"))'
endif

if !exists("g:slimv_template_describe")
    let g:slimv_template_describe = '(describe (read-from-string "%1"))'
endif

if !exists("g:slimv_template_trace")
    let g:slimv_template_trace = "(trace %1)"
endif

if !exists("g:slimv_template_untrace")
    let g:slimv_template_untrace = "(untrace %1)"
endif

if !exists("g:slimv_template_profile")
    "TODO: support different Lisp implementations
    let g:slimv_template_profile = "(mon:monitor %1)"
endif

if !exists("g:slimv_template_unprofile")
    "TODO: support different Lisp implementations
    let g:slimv_template_unprofile = "(mon:unmonitor %1)"
endif

if !exists("g:slimv_template_disassemble")
    let g:slimv_template_disassemble = "(disassemble #'%1)"
endif

if !exists("g:slimv_template_apropos")
    let g:slimv_template_apropos = '(apropos "%1")'
endif

if !exists("g:slimv_template_macroexpand")
    let g:slimv_template_macroexpand = '(pprint %1)'
endif

if !exists("g:slimv_template_macroexpand_all")
    let g:slimv_template_macroexpand_all = '(pprint %1)'
endif

if !exists("g:slimv_template_compile_file")
"    let g:slimv_template_compile_file = '(compile-file "%1")'
    let g:slimv_template_compile_file =
    \ '(let ((fasl-file (compile-file "%1")))' .
    \ '	 (when (and %2 fasl-file) (load fasl-file)))'
endif

if !exists("g:slimv_template_compile_string")
    let g:slimv_template_compile_string = 
    \ '(funcall (compile nil (read-from-string (format nil "(~S () ~A)" ' . "'" . 'lambda "%1"))))'
endif

if !exists("mapleader")
    let mapleader = ','
endif


" =====================================================================
"  General utility functions
" =====================================================================

"function! SlimvServerRunning()
"    "TODO: make this work on Linux
"    let netstat = system( 'netstat -a' )
"    "let netstat = execute '!netstat -a'
"    if match( netstat, printf( '%d', g:slimv_port ) ) >= 0
"	return 1
"    else
"	return 0
"endfunction

"function! SlimvConnectServer()
"    "TODO: make this work on Linux
"    "TODO: handle if called again after server already started
"    "silent execute ":!start " . g:slimv_server
"    silent execute g:slimv_server
"    " Wait for server + Lisp startup
"    sleep 1
"endfunction

" Load Python library and necessary modules
function! SlimvLoad()
""echo 'console -r "/k %p \"%s\" -l %l -s"'
    if g:slimv_loaded_python == 0
        "py import vim
        "py import sys
        "py import os
        let g:slimv_loaded_python = 1
"	call SlimvConnectServer()
    endif
endfunction

" Select symbol under cursor and copy it to register 's'
function! SlimvSelectSymbol()
    "TODO: can we use expand('<cWORD>') here?
    normal viw"sy
endfunction

" Select bottom level form the cursor is inside and copy it to register 's'
function! SlimvSelectForm()
    "normal va("sy
    normal va(o
    " Handle '() or #'() etc. type special syntax forms
    " TODO: what to do with ` operator?
    let c = col(".") - 2
    while c > 0 && match(' \t()', getline(".")[c]) < 0
        normal h
	let c = c - 1
    endwhile
    normal "sy
endfunction

" Select top level form the cursor is inside and copy it to register 's'
function! SlimvSelectToplevelForm()
    normal 99[(
    call SlimvSelectForm()
endfunction

" Return the contents of register 's'
function! SlimvGetSelection()
    return getreg('"s')
endfunction

function SlimvMakeArgs(args)
    "echo a:args
    let ar = a:args
    let i = 0
    while i < len(ar)
	let ar[i] = substitute(ar[i], '"',  '\\"', 'g')
	let i = i + 1
    endwhile
    let a = join(ar, '" "')
    "let a = substitute(a, '"',  '\\"', 'g')
    let a = substitute(a, '\n', '\\n', 'g')
    let a = '"' . a . '" '
    "let a = ''
    ""let a = a . '"' . substitute(a:args[0], '\n', '\\n" "', 'g') . '" '
    "let a = a . '"' . substitute(a:args[0], '\n', '\\n', 'g') . '" '
    "TODO: debug option: printout here
    "echo a
    return a
endfunction

function! SlimvSendToClient(args)
    let result = system( g:slimv_client . ' -c ' . SlimvMakeArgs(a:args) )
    "TODO: debug option: keep client window open
"    execute '!' . g:slimv_client . SlimvMakeArgs(a:args)
endfunction

" Send argument to Lisp server for evaluation
function! SlimvEval(args)
    "TODO: overcome command line argument length limitations
    "TODO: in visual mode and not called from EvalRegion do not call this in a
    "      loop for all lines in the selection
    call SlimvLoad()

    if g:slimv_client == ''
	" No command to start client, we are clueless, ask user for assistance
	if g:slimv_python == ''
	    let g:slimv_python = input( "Enter Python path (or fill g:slimv_python in your vimrc): ", "", "file" )
	endif
	if g:slimv_lisp == ''
	    let g:slimv_lisp = input( "Enter Lisp path (or fill g:slimv_lisp in your vimrc): ", "", "file" )
	endif
	let g:slimv_client = SlimvClientCommand()
    endif

    if g:slimv_client != ''
" start client with server command given
"    py sys.argv = [vim.eval("g:slimv_path"),
"                  \ '-r', vim.eval("g:slimv_server"), '-c'] + 
"                  \ vim.eval("a:args")
    "call SlimvMakeArgs(a:args)
    "py sys.argv = [vim.eval("g:slimv_path"), '-c'] + vim.eval("a:args")
    "execute ":pyfile " . g:slimv_path
"    silent execute '!' . g:slimv_python . ' "' . g:slimv_path . '" -c "(+ 1 2)"'
"    echo '!' . g:slimv_python . ' "' . g:slimv_path . '" -c ' . SlimvMakeArgs(a:args)

    "silent execute '!' . g:slimv_python . ' "' . g:slimv_path . '" -c ' . SlimvMakeArgs(a:args)
"    silent execute g:slimv_client . SlimvMakeArgs(a:args)
    "TODO: why does the followign give an E371: Command not found error on Windows?
    "silent execute ':!start /WAIT /B ' . g:slimv_python . ' "' . g:slimv_path . '" -c ' . SlimvMakeArgs(a:args)
    "silent execute '!cmd /c /q ' . g:slimv_python . ' "' . g:slimv_path . '" -c ' . SlimvMakeArgs(a:args)
    "execute '!' . g:slimv_python . ' "' . g:slimv_path . '" -c ' . SlimvMakeArgs(a:args)

    "let result = system( g:slimv_client . SlimvMakeArgs(a:args) )
    "let result = system( g:slimv_python . ' "' . g:slimv_path . '" -c ' . SlimvMakeArgs(a:args) )

    let use_temp_file = 1
    if use_temp_file
	"TODO: option to set explicit temp file name and delete/keep after usage
	let tmp = tempname()
	"let tmp = "c:/Progra~1/Vim/vimfiles/plugin/slimv.tmp"
	try
	    call writefile( a:args, tmp )
	    let result = system( g:slimv_client . ' -f ' . tmp )
"	    echo tmp
	finally
"	    call delete(tmp)
	endtry
    else

	let total = 0
	let i = 0
	let j = 0
	while j < len( a:args )
	    let l = len( a:args[j] )
	    if l >= 1000
		" Check the length of each line
		echo 'Line #' . j . ' too long'
		break
	    endif
	    if total + l < 1000
		" Limit also total length to be passed to the client
		" in command line args
		let total = total + l
	    else
		" Total length would be too large, pass lines collected previously
		" and start over collecting lines
		call SlimvSendToClient(a:args[i : j-1])
		let i = j
		let total = 0
	    endif
	    let j = j + 1
	endwhile
	if i < j
	    " There are some lines left unsent, send them now
	    call SlimvSendToClient(a:args[i : j-1])
	endif
"	echo g:slimv_client . SlimvMakeArgs(a:args)
"	    let result = system( g:slimv_client . SlimvMakeArgs(a:args) )
	"TODO: debug option: keep client window open
"	execute '!' . g:slimv_client . SlimvMakeArgs(a:args)
	"echo result
    endif
    endif
endfunction

function! SlimvConnectServer()
    call SlimvEval([";;; Slimv client connected successfully"])
endfunction

function! SlimvGetRegion() range
    "TODO: handle continuous (not whole line) selection case
    "TODO: getline has only one argument in VIM 6.x
    if mode() == "v" || mode() == "V"
        let lines = getline(a:firstline, a:lastline)
	let firstcol = col(a:firstline) - 1
	let lastcol  = col(a:lastline ) - 2
    else
        let lines = getline("'<", "'>")
	let firstcol = col("'<") - 1
	let lastcol  = col("'>") - 2
    endif
    if lastcol >= 0
	let lines[len(lines)-1] = lines[len(lines)-1][ : lastcol]
    else
	let lines[len(lines)-1] = ''
    endif
    let lines[0] = lines[0][firstcol : ]
    return lines
endfunction

" Eval buffer lines in the given range
function! SlimvEvalRegion() range
    "TODO: handle continuous (not whole line) selection case
    "TODO: getline has only one argument in VIM 6.x
    if mode() == "v" || mode() == "V"
        let lines = getline(a:firstline, a:lastline)
	let firstcol = col(a:firstline) - 1
	let lastcol  = col(a:lastline ) - 2
    else
        let lines = getline("'<", "'>")
	let firstcol = col("'<") - 1
	let lastcol  = col("'>") - 2
    endif
    if lastcol >= 0
	let lines[len(lines)-1] = lines[len(lines)-1][ : lastcol]
    else
	let lines[len(lines)-1] = ''
    endif
    let lines[0] = lines[0][firstcol : ]
    call SlimvEval(lines)
endfunction

" Eval contents of the 's' register
function! SlimvEvalSelection()
    "TODO: VIM 6.x does not have lists. What to do?
    let lines = [SlimvGetSelection()]
    "let lines = []
    "call add(lines, SlimvGetSelection())
    call SlimvEval(lines)
endfunction

" Eval Lisp form.
" Form given in the template is passed to Lisp without modification.
function! SlimvEvalForm(template)
    let lines = [a:template]
    call SlimvEval(lines)
endfunction

" Eval Lisp form, with the given parameter substituted in the template.
" %1 string is substituted with par1
function! SlimvEvalForm1(template, par1)
    "let p1 = substitute(a:par1, '&', '\\&', "g")  " & -> \&
    let p1 = escape(a:par1, '&')
    let p1 = escape(p1, '\\')
    let temp1 = substitute(a:template, '%1', p1, "g")
    let lines = [temp1]
    call SlimvEval(lines)
endfunction

" Eval Lisp form, with the given parameters substituted in the template.
" %1 string is substituted with par1
" %2 string is substituted with par2
function! SlimvEvalForm2(template, par1, par2)
    "let p1 = substitute(a:par1, '&', '\\&', "g")  " & -> \&
    "let p2 = substitute(a:par2, '&', '\\&', "g")  " & -> \&
    "echo a:par1
    let p1 = escape(a:par1, '&')
    let p2 = escape(a:par2, '&')
    "echo p1
    let p1 = escape(p1, '\\')
    let p2 = escape(p2, '\\')
    "echo p1
    let temp1 = substitute(a:template, '%1', p1, "g")
    "echo temp1
    let temp2 = substitute(temp1,      '%2', p2, "g")
    let lines = [temp2]
    call SlimvEval(lines)
endfunction

" =====================================================================
"  Special functions
" =====================================================================

function! SlimvEvalDefun()
    call SlimvSelectToplevelForm()
    call SlimvEvalSelection()
endfunction

" Evaluate the whole buffer
function! SlimvEvalBuffer()
    let lines = getline(1, '$')
    call SlimvEval(lines)
endfunction

function! SlimvEvalLastExp()
    call SlimvSelectForm()
    call SlimvEvalSelection()
endfunction

function! SlimvPprintEvalLastExp()
    call SlimvSelectForm()
    call SlimvEvalForm1(g:slimv_template_pprint, SlimvGetSelection())
endfunction

function! SlimvInteractiveEval()
    let e = input( "Eval: " )
    if e != ""
        call SlimvEval([e])
    endif
endfunction

function! SlimvUndefineFunction()
    call SlimvSelectSymbol()
    call SlimvEvalForm1(g:slimv_template_undefine, SlimvGetSelection())
endfunction

" ---------------------------------------------------------------------

function! SlimvMacroexpand()
    normal 99[(vt(%"sy
    let m = SlimvGetSelection() . "))"
    let m = substitute(m, "defmacro\\s*", "macroexpand-1 '(", "g")
    call SlimvEvalForm1(g:slimv_template_macroexpand, m)
endfunction

function! SlimvMacroexpandAll()
    normal 99[(vt(%"sy
    let m = SlimvGetSelection() . "))"
    let m = substitute(m, "defmacro\\s*", "macroexpand '(", "g")
    call SlimvEvalForm1(g:slimv_template_macroexpand_all, m)
endfunction

function! SlimvTrace()
    call SlimvSelectSymbol()
    let s = input( "Trace: ", SlimvGetSelection() )
    echo s
    if s != ""
        call SlimvEvalForm1(g:slimv_template_trace, s)
    endif
endfunction

function! SlimvUntrace()
    call SlimvSelectSymbol()
    let s = input( "Untrace: ", SlimvGetSelection() )
    if s != ""
        call SlimvEvalForm1(g:slimv_template_untrace, s)
    endif
endfunction

function! SlimvDisassemble()
    call SlimvSelectSymbol()
    let s = input( "Disassemble: ", SlimvGetSelection() )
    if s != ""
        call SlimvEvalForm1(g:slimv_template_disassemble, s)
    endif
endfunction

function! SlimvProfile()
    call SlimvSelectSymbol()
    let s = input( "Profile: ", SlimvGetSelection() )
    if s != ""
        call SlimvEvalForm1(g:slimv_template_profile, s)
    endif
endfunction

function! SlimvUnProfile()
    call SlimvSelectSymbol()
    let s = input( "Unprofile: ", SlimvGetSelection() )
    if s != ""
        call SlimvEvalForm1(g:slimv_template_unprofile, s)
    endif
endfunction

" ---------------------------------------------------------------------

" compile-string
"      (funcall (compile nil (read-from-string
"                             (format nil "(~S () ~A)" 'lambda string)


function! SlimvCompileDefun()
    "TODO: handle double quote characters in form
    call SlimvSelectToplevelForm()
    call SlimvEvalForm1(g:slimv_template_compile_string, SlimvGetSelection())
endfunction

function! SlimvCompileLoadFile()
    let filename = fnamemodify(bufname(""), ":p")
    let filename = escape(filename, '\\')
    call SlimvEvalForm2(g:slimv_template_compile_file, filename, "T")
endfunction

function! SlimvCompileFile()
    let filename = fnamemodify(bufname(""), ":p")
    let filename = escape(filename, '\\')
    call SlimvEvalForm2(g:slimv_template_compile_file, filename, "NIL")
endfunction

function! SlimvCompileRegion() range
    "TODO: handle double quote characters in form
    let lines = SlimvGetRegion()
    let region = join(lines, ' ')
    call SlimvEvalForm1(g:slimv_template_compile_string, region)
endfunction

function! SlimvDescribeSymbol()
    call SlimvSelectSymbol()
    call SlimvEvalForm1(g:slimv_template_describe, SlimvGetSelection())
endfunction

" ---------------------------------------------------------------------

function! SlimvApropos()
    call SlimvSelectSymbol()
    call SlimvEvalForm1(g:slimv_template_apropos, SlimvGetSelection())
endfunction

" =====================================================================
"  Slimv keybindings
" =====================================================================

" <Leader> can be set in .vimrc, it defaults here to ','
" <Leader> timeouts in 1000 msec by default, if this is too short,
" then increase 'timeoutlen'
map <Leader>S  :call SlimvConnectServer()<CR>

map <Leader>d  :call SlimvEvalDefun()<CR>
map <Leader>e  :call SlimvEvalLastExp()<CR>
map <Leader>E  :call SlimvPprintEvalLastExp()<CR>
map <Leader>r  :call SlimvEvalRegion()<CR>
map <Leader>b  :call SlimvEvalBuffer()<CR>
map <Leader>i  :call SlimvInteractiveEval()<CR>
map <Leader>u  :call SlimvUndefineFunction()<CR>

map <Leader>1  :call SlimvMacroexpand()<CR>
map <Leader>m  :call SlimvMacroexpandAll()<CR>
map <Leader>t  :call SlimvTrace()<CR>
map <Leader>T  :call SlimvUntrace()<CR>
map <Leader>l  :call SlimvDisassemble()<CR>

map <Leader>D  :call SlimvCompileDefun()<CR>
map <Leader>L  :call SlimvCompileLoadFile()<CR>
map <Leader>F  :call SlimvCompileFile()<CR>
map <Leader>R  :call SlimvCompileRegion()<CR>

map <Leader>p  :call SlimvProfile()<CR>
map <Leader>P  :call SlimvUnprofile()<CR>

map <Leader>s  :call SlimvDescribeSymbol()<CR>
map <Leader>a  :call SlimvApropos()<CR>

" =====================================================================
"  Slimv menu
" =====================================================================

" Works only if 'wildcharm' is <Tab>
":map <Leader>, :emenu Slimv.<Tab>
if &wildcharm == 0
    set wildcharm=<Tab>
endif
if &wildcharm != 0
    execute ":map <Leader>, :emenu Slimv." . nr2char(&wildcharm)
endif

menu &Slimv.&Evaluation.Eval-&Defun                :call SlimvEvalDefun()<CR>
menu &Slimv.&Evaluation.Eval-Last-&Exp             :call SlimvEvalLastExp()<CR>
menu &Slimv.&Evaluation.&Pprint-Eval-Last          :call SlimvPprintEvalLastExp()<CR>
menu &Slimv.&Evaluation.Eval-&Region               :call SlimvEvalRegion()<CR>
menu &Slimv.&Evaluation.Eval-&Buffer               :call SlimvEvalBuffer()<CR>
menu &Slimv.&Evaluation.&Interactive-Eval\.\.\.    :call SlimvInteractiveEval()<CR>
menu &Slimv.&Evaluation.&Undefine-Function         :call SlimvUndefineFunction()<CR>

menu &Slimv.De&bugging.Macroexpand-&1              :call SlimvMacroexpand()<CR>
menu &Slimv.De&bugging.&Macroexpand-All            :call SlimvMacroexpandAll()<CR>
menu &Slimv.De&bugging.&Trace\.\.\.                :call SlimvTrace()<CR>
menu &Slimv.De&bugging.U&ntrace\.\.\.              :call SlimvUntrace()<CR>
menu &Slimv.De&bugging.Disassemb&le\.\.\.          :call SlimvDisassemble()<CR>

menu &Slimv.&Compilation.Compile-&Defun            :call SlimvCompileDefun()<CR>
menu &Slimv.&Compilation.Compile-&Load-File        :call SlimvCompileLoadFile()<CR>
menu &Slimv.&Compilation.Compile-&File             :call SlimvCompileFile()<CR>
menu &Slimv.&Compilation.Compile-&Region           :call SlimvCompileRegion()<CR>

menu &Slimv.&Profiling.&Profile\.\.\.              :call SlimvProfile()<CR>
menu &Slimv.&Profiling.&Unprofile\.\.\.            :call SlimvUnprofile()<CR>

menu &Slimv.&Documentation.Describe-&Symbol        :call SlimvDescribeSymbol()<CR>
menu &Slimv.&Documentation.&Apropos                :call SlimvApropos()<CR>
