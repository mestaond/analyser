from app.gui import streamlitapp as sapp
import sys
from streamlit import cli as stcli
import streamlit


# inspired by StackOverflow
if __name__ == '__main__':
    if streamlit._is_running_with_streamlit:
        sapp.main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
