#!/bin/bash

if [[ -f hi.txt ]]; then
	echo "exists"
	exit 0
fi

echo "not exists"
exit 1
