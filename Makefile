all: cloc.py
	pyinstaller --onefile cloc.py && mv dist/cloc ./ && rm -rf dist/ build/ && mv cloc /usr/local/bin/
