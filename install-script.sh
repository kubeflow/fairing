#!/bin/sh

curl -L https://github.com/wbuchwalter/metaparticle-ast/releases/download/v0.5.0/mp-compiler-linux-amd64.tar.gz -o mp-compiler-linux-amd64.tar.gz
tar -zxf mp-compiler-linux-amd64.tar.gz
rm mp-compiler-linux-amd64.tar.gz
mv mp-compiler /usr/local/bin
