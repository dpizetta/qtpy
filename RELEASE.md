To release a new version of qtpy on PyPI:

* Close Github milestone

* git fetch upstream && git merge upstream/master

* git clean -xfdi

* Update CHANGELOG.md

* Update `_version.py` (set release version, remove 'dev0')

* git add and git commit

* python setup.py sdist

* python setup.py bdist_wheel

* twine upload dist/*

* git tag -a vX.X.X -m 'comment'

* Update `_version.py` (add 'dev0' and increment minor)

* git add and git commit

* git push

* git push --tags
