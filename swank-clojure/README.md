# Swank Clojure

[Swank Clojure](http://github.com/technomancy/swank-clojure) is a
server that allows [SLIME](http://common-lisp.net/project/slime/) (the
Superior Lisp Interaction Mode for Emacs) to connect to Clojure
projects.

## Usage

The simplest way is to just <tt>jack-in</tt> from an existing project
using [Leiningen](http://github.com/technomancy/leiningen):

* Install clojure-mode either from
  [Marmalade](http://marmalade-repo.org) or from
  [git](http://github.com/technomancy/clojure-mode).
* <tt>lein plugin install swank-clojure 1.3.2</tt>
* From inside a project, invoke <tt>M-x clojure-jack-in</tt>

That's all it takes! There are no extra install steps beyond
clojure-mode on the Emacs side and the swank-clojure plugin on the
Leiningen side.

## SLIME Commands

Commonly-used SLIME commands:

* **C-c TAB**: Autocomplete symbol at point
* **C-x C-e**: Eval the form under the point
* **C-c C-k**: Compile the current buffer
* **C-c C-l**: Load current buffer and force required namespaces to reload
* **M-.**: Jump to the definition of a var
* **C-c S-i**: Inspect a value
* **C-c C-m**: Macroexpand the call under the point
* **C-c C-d C-d**: Look up documentation for a var
* **C-c C-z**: Switch from a Clojure buffer to the repl buffer
* **C-c M-p**: Switch the repl namespace to match the current buffer
* **C-c C-w c**: List all callers of a given function

Pressing "v" on a stack trace a debug buffer will jump to the file and
line referenced by that frame if possible.

Note that SLIME was designed to work with Common Lisp, which has a
distinction between interpreted code and compiled code. Clojure has no
such distinction, so the load-file functionality is overloaded to add
<code>:reload-all</code> behaviour.

## Alternate Usage

There are other ways to use Swank for different specific
circumstances.  For each of these methods you will have to install
slime and slime-repl manually as outlined in "Connecting with SLIME"
below.

### Standalone Server

If you just want a standalone swank server with no third-party
libraries, you can use the shell wrapper that Leiningen installs for
you:

    $ lein plugin install swank-clojure 1.3.2
    $ ~/.lein/bin/swank-clojure

    M-x slime-connect

If you put ~/.lein/bin on your $PATH it's even more convenient.

### Manual Swank in Project

You can also start a swank server from inside your project.
You'll need to either have installed using <tt>lein plugin
install</tt> or have added swank-clojure to project.clj:

    [swank-clojure "1.3.2"]

Then launch the server:

    $ lein swank # you can specify PORT and HOST optionally

If you're using Maven, add this to your pom.xml under the
\<dependencies\> section:

    <dependency>
      <groupId>swank-clojure</groupId>
      <artifactId>swank-clojure</artifactId>
      <version>1.3.2</version>
    </dependency>

Then you can launch a swank server like so:

    $ mvn clojure:swank

Note that due to a bug in clojure-maven-plugin, you currently cannot
include it as a test-scoped dependency; it must be compile-scoped. You
also cannot change the port from Maven; it's hard-coded to 4005.

Put this in your Emacs configuration to get syntax highlighting in the
slime repl:

    (add-hook 'slime-repl-mode-hook 'clojure-mode-font-lock-setup)

## Connecting with SLIME

If you're not using the <tt>M-x clojure-jack-in</tt> method mentioned
above, you'll have to install SLIME yourself. The easiest way is to
use package.el. If you are using Emacs 24 or the
[Emacs Starter Kit](http://github.com/technomancy/emacs-starter-kit),
then you have it already. If not, get it
[from Emacs's own repository](http://bit.ly/pkg-el23).

Then add Marmalade as an archive source in your Emacs config:

    (require 'package)
    (add-to-list 'package-archives
                 '("marmalade" . "http://marmalade-repo.org/packages/") t)

Then you can do <kbd>M-x package-list-packages</kbd>. Go down to
slime-repl and mark it with <kbd>i</kbd>. Execute the installation by
pressing <kbd>x</kbd>.

When you perform the installation, you will see warnings related to
the byte-compilation of the packages. This is **normal**; the packages
will work just fine even if there are problems byte-compiling it upon
installation.

Then you should be able to connect to the swank server you launched:

    M-x slime-connect

It will prompt you for your host (usually localhost) and port. It may
also warn you that your SLIME version doesn't match your Swank
version; this should be OK.

Having old versions of SLIME either manually installed or installed
using a system-wide package manager like apt-get may cause
issues. Also the official CVS version of SLIME is not supported; it
often breaks compatibility with Clojure.

## Embedding

You can embed Swank Clojure in your project, start the server from
within your own code, and connect via Emacs to that instance:

    (ns my-app
      (:require [swank.swank]))
    (swank.swank/start-repl) ;; optionally takes a port argument

Then use M-x slime-connect to connect from within Emacs.

You can also start the server directly from the "java" command-line
launcher if you AOT-compile it and specify "swank.swank" as your main
class.

## Debugging

You can set repl-aware breakpoints using <tt>swank.core/break</tt>.
For now, see
[Hugo Duncan's blog](http://hugoduncan.org/post/2010/swank_clojure_gets_a_break_with_the_local_environment.xhtml)
for an explanation of this excellent feature.

[CDT](http://georgejahad.com/clojure/swank-cdt.html) (included in
Swank Clojure since 1.4.0) is a more comprehensive debugging tool
that includes support for stepping, seting breakpoints, catching
exceptions, and eval clojure expressions in the context of the current
lexical scope.

## Community

The [mailing list](http://groups.google.com/group/swank-clojure) and
clojure channel on Freenode are the best places to bring up
questions/issues.

Contributions are preferred as either Github pull requests or using
"git format-patch". Please use standard indentation with no tabs,
trailing whitespace, or lines longer than 80 columns. See [this post
on submitting good patches](http://technomancy.us/135) for some
tips. If you've got some time on your hands, reading this [style
guide](http://mumble.net/~campbell/scheme/style.txt) wouldn't hurt
either.

## License

Copyright (C) 2008-2011 Jeffrey Chu, Phil Hagelberg, Hugo Duncan, and
contributors

Licensed under the EPL. (See the file COPYING.)
