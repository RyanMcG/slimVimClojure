" slimv-clojure.vim:
"               Clojure filetype plugin for Slimv
" Version:      0.5.0
" Last Change:  31 Mar 2009
" Maintainer:   Tamas Kovacs <kovisoft at gmail dot com>
" License:      This file is placed in the public domain.
"               No warranty, express or implied.
"               *** ***   Use At-Your-Own-Risk!   *** ***
"
" =====================================================================
"
"  Load Once:
if &cp || exists( 'g:slimv_clojure_loaded' )
    finish
endif

let g:slimv_clojure_loaded = 1

runtime ftplugin/**/slimv.vim

