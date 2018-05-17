from dicommodule.Patient_Catheter import CatheterObj
import numpy as np

dummyPoint = np.array([84.681462, 47.232167, -30.138217])
dummyPoints = np.array([[95.769797, 43.011019, 3.208849],
                        [90.757262, 45.965823, -14.097856],
                        [84.681462, 47.232167, -30.138217],
                        [82.403037, 48.498511, -45.967521],
                        [82.151345, 48.671564, -59.242360]])
dummyShape = dummyPoints.shape

row, col = (4, 'D')
template_coord_string = '{}{}'.format(col, row)


def test_catheter_create_empty():
    cath = CatheterObj(row, col)
    assert cath.has_data() is False


def test_catheter_add_single_point():
    cath = CatheterObj(row, col)
    cath.add_raw_measurement(dummyPoint)
    assert cath.has_data() is True
    assert cath.get_N_raw_pts() == 1


def test_catheter_adding_multi_points():
    cath = CatheterObj(row, col)
    assert cath.add_raw_measurement(dummyPoints) is True
    assert cath.has_data() is True
    assert cath.get_N_raw_pts() == 5
    assert cath.get_raw_data().shape == dummyShape


def test_close_catheter():
    cath = CatheterObj(row, col)
    assert cath.add_raw_measurement(dummyPoints) is True
    assert cath.finishMeasuring() is True
    assert cath.add_raw_measurement(dummyPoints) is False


def test_premature_closure():
    cath = CatheterObj(row, col)
    assert cath.finishMeasuring() is False


def test_template_assignment():
    cath = CatheterObj(row, col)
    assert cath.getTemplateAlphanumeric() == template_coord_string


def test_get_VirtualCatheter():
    cath = CatheterObj(row, col)
    assert cath.to_virtual_catheter().shape[0] == 4

# def test_return_points():
