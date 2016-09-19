#!/usr/bin/env bash

BAG_FILES=`find $1 -iname '*.bag'`

for bag in $BAG_FILES; do
  if [  ! -e $bag.md5 ]; then
    echo Generating md5sum for $bag
    bagfile=`basename $bag`
    bagdir=`dirname $bag`    
    (cd $bagdir && exec md5sum $bagfile > $bagfile.md5)
  fi
done
