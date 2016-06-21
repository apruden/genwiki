import os, sys
from genwiki.genwiki import main

if __name__ == '__main__':
    if os.name == 'nt':
        from genwiki.windows import run_as_windows_service
        if len(sys.argv) > 1:
            run_as_windows_service()
        else:
            main()
    else:
        main(reloader=True)
