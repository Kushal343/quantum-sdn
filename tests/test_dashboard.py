from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_dashboard_runs_small_experiment():
    app = AppTest.from_file(str(Path(__file__).parents[1] / 'dashboard.py'), default_timeout=120)
    app.run()
    assert not app.exception
    app.slider[0].set_value(4)
    app.select_slider[0].set_value(2000)
    app.button[0].click().run()
    assert not app.exception
    assert len(app.metric) == 3
    assert len(app.session_state['experiment'][0]) == 16
