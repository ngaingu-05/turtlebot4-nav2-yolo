import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from gesture_core import Controller, WaveDetector


def hold(c, gesture, t, sim=0):
    c.receive(gesture, t, sim)
    c.receive(gesture, t + .36, sim)


def test_confirmation_and_no_repeat():
    c = Controller()
    hold(c, 'Pointing_Up', 0)
    assert c.velocity(.4, 0) == (0., 0.)
    hold(c, 'Thumb_Up', .5)
    assert c.velocity(.9, 0)[0] > 0
    assert c.velocity(.9, 1.5)[0] < 0
    assert c.velocity(.9, 12) == (0., 0.)
    c.receive('Thumb_Up', 1, 13)
    assert c.active is None


def test_stop_cancel_loss_clear_selection():
    for stop in ['Open_Palm', 'Closed_Fist']:
        c = Controller()
        hold(c, 'Victory', 0)
        hold(c, 'Thumb_Up', .5)
        c.receive(stop, .9, 0)
        assert c.velocity(.9, 0) == (0., 0.)
        assert c.selected is None
    c = Controller()
    hold(c, 'Victory', 0)
    hold(c, 'Thumb_Up', .5)
    c.receive('None', 1, 0)
    assert c.velocity(1.7, 0) == (0., 0.)
    assert c.active is None


def test_noise_and_circle_completion():
    c = Controller()
    for i in range(10):
        c.receive('Victory' if i % 2 else 'Pointing_Up', i * .1, 0)
    assert c.selected is None
    hold(c, 'Victory', 2)
    hold(c, 'Thumb_Up', 2.5)
    assert c.velocity(2.9, 0) == (.12, .3)
    assert c.velocity(2.9, 21) == (0., 0.)


def test_wave_temporal_and_stationary_palm():
    w = WaveDetector()
    for i in range(20):
        assert w.update('Open_Palm', .5, i * .05) == 'Open_Palm'
    labels = [w.update('Open_Palm', x, 2 + i * .1)
              for i, x in enumerate([.2, .4, .6, .4, .2, .4, .6])]
    assert 'Wave' in labels
    assert w.update('Closed_Fist', .5, 3) == 'Closed_Fist'


def test_clock_reset():
    c = Controller()
    hold(c, 'Wave', 0, 10)
    hold(c, 'Thumb_Up', .5, 10)
    assert c.velocity(.9, 9) == (0., 0.)


def test_selection_survives_hand_transition_but_expires():
    c = Controller()
    hold(c, 'Victory', 0)
    c.receive('None', .5, 0)
    assert c.velocity(1.5, 0) == (0., 0.)
    assert c.selected == 'circle'
    hold(c, 'Thumb_Up', 1.6)
    assert c.velocity(2., 0) == (.12, .3)
    assert c.velocity(2.8, 0) == (0., 0.)
    c = Controller()
    hold(c, 'Victory', 0)
    c.velocity(5.5, 0)
    hold(c, 'Thumb_Up', 5.6)
    assert c.active is None and c.selected is None


def test_holding_selection_refreshes_confirmation_window():
    c = Controller()
    hold(c, 'Victory', 0)
    c.receive('Victory', 10., 0)
    c.velocity(10., 0)
    assert c.selected == 'circle'
    hold(c, 'Thumb_Up', 11.)
    assert c.velocity(11.4, 0) == (.12, .3)
