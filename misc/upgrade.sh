#!/bin/sh
[ -f manage.py ] || exit
python3 manage.py migrate --plan

while true; do
	read -p "Do you wish to continue? (yes/no) " yn
	case $yn in
		[Yy]* ) break;;
		[Nn]* ) exit;;
	esac
done

python3 manage.py sass common/static/sass/boofilsic.sass common/static/css/boofilsic.min.css -t compressed || exit $?
python3 manage.py sass common/static/sass/boofilsic.sass common/static/css/boofilsic.css || exit $?
python3 manage.py collectstatic --noinput || exit $?
python3 manage.py migrate || exit $?
python3 manage.py check
