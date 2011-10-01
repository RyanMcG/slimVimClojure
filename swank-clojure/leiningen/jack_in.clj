(ns leiningen.jack-in
  (:use [leiningen.compile :only [eval-in-project]]
        [leiningen.swank :only [swank]])
  (:require [clojure.java.io :as io]
            [clojure.string :as string])
  (:import (java.util.jar JarFile)))

(defn- get-manifest [file]
  (let [attrs (-> file JarFile. .getManifest .getMainAttributes)]
    (zipmap (map str (keys attrs)) (vals attrs))))

(defn- get-payloads [file]
  (.split (get (get-manifest file) "Swank-Elisp-Payload") " "))

(defn elisp-payload-files []
  ["swank/payload/slime.el" "swank/payload/slime-repl.el"]
  #_(apply concat ["swank/payload/slime.el" "swank/payload/slime-repl.el"]
           (->> (scan-paths (System/getProperty "sun.boot.class.path")
                            (System/getProperty "java.ext.dirs")
                            (System/getProperty "java.class.path"))
                (filter #(jar-file? (.getName (:file %))))
                (get-payloads))))

(defn payloads []
  (for [file (elisp-payload-files)]
    (slurp (io/resource file))))

(defn jack-in
  "Jack in to a Clojure SLIME session from Emacs.

This task is intended to be launched from Emacs using M-x clojure-jack-in,
which is part of the clojure-mode library."
  [project port]
  (println ";;; Bootstrapping bundled version of SLIME; please wait...\n\n")
  (println (string/join "\n" (payloads)))
  (println "(run-hooks 'slime-load-hook)")
  (swank project port "localhost" ":message" "\";;; proceed to jack in\""))
