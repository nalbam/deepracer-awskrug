import math


MODE = "shortcut"  # center, shortcut

MAX_SIGHT = 1.0


def dist(point1, point2):
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5


# thanks to https://stackoverflow.com/questions/20924085/python-conversion-between-coordinates
def rect(r, theta):
    """
    theta in degrees
    returns tuple; (float, float); (x,y)
    """

    x = r * math.cos(math.radians(theta))
    y = r * math.sin(math.radians(theta))
    return x, y


# thanks to https://stackoverflow.com/questions/20924085/python-conversion-between-coordinates
def polar(x, y):
    """
    returns r, theta(degrees)
    """

    r = (x ** 2 + y ** 2) ** 0.5
    theta = math.degrees(math.atan2(y, x))
    return r, theta


def angle_mod_360(angle):
    """
    Maps an angle to the interval -180, +180.
    Examples:
    angle_mod_360(362) == 2
    angle_mod_360(270) == -90
    :param angle: angle in degree
    :return: angle in degree. Between -180 and +180
    """

    n = math.floor(angle / 360.0)

    angle_between_0_and_360 = angle - n * 360.0

    if angle_between_0_and_360 <= 180.0:
        return angle_between_0_and_360
    else:
        return angle_between_0_and_360 - 360


def get_waypoints_ordered_in_driving_direction(params):
    if MODE == "shortcut":
        waypoints = get_shortcut_waypoints()
    else:
        waypoints = params["waypoints"]

    # waypoints are always provided in counter clock wise order
    if params["is_reversed"]:  # driving clock wise.
        return list(reversed(waypoints))
    else:  # driving counter clock wise.
        return waypoints


def up_sample(waypoints, factor=10):
    """
    Adds extra waypoints in between provided waypoints
    :param waypoints:
    :param factor: integer. E.g. 3 means that the resulting list has 3 times as many points.
    :return:
    """
    p = waypoints
    n = len(p)

    return [
        [
            i / factor * p[int((j + 1) % n)][0] + (1 - i / factor) * p[j][0],
            i / factor * p[int((j + 1) % n)][1] + (1 - i / factor) * p[j][1],
        ]
        for j in range(n)
        for i in range(factor)
    ]


def get_target_point(params):
    waypoints = up_sample(get_waypoints_ordered_in_driving_direction(params), 20)

    car = [params["x"], params["y"]]

    distances = [dist(p, car) for p in waypoints]
    min_dist = min(distances)
    i_closest = distances.index(min_dist)

    n = len(waypoints)

    waypoints_starting_with_closest = [waypoints[(i + i_closest) % n] for i in range(n)]

    if MODE == "shortcut":
        sight = MAX_SIGHT * 0.5
    else:
        sight = MAX_SIGHT

    r = params["track_width"] * sight

    is_inside = [dist(p, car) < r for p in waypoints_starting_with_closest]
    i_first_outside = is_inside.index(False)

    if i_first_outside < 0:
        # this can only happen if we choose r as big as the entire track
        return waypoints[i_closest]

    return waypoints_starting_with_closest[i_first_outside]


def get_target_steering_degree(params):
    tx, ty = get_target_point(params)
    car_x = params["x"]
    car_y = params["y"]
    dx = tx - car_x
    dy = ty - car_y
    heading = params["heading"]

    _, target_angle = polar(dx, dy)

    steering_angle = target_angle - heading

    return angle_mod_360(steering_angle)


def score_steer_to_point_ahead(params):
    best_stearing_angle = get_target_steering_degree(params)
    steering_angle = params["steering_angle"]

    error = (
        steering_angle - best_stearing_angle
    ) / 60.0  # 60 degree is already really bad

    score = 1.0 - abs(error)

    return max(
        score, 0.01
    )  # optimizer is rumored to struggle with negative numbers and numbers too close to zero


def reward_function(params):
    return float(score_steer_to_point_ahead(params))


def get_test_params():
    return {
        "x": 0.7,
        "y": 1.05,
        "heading": 160.0,
        "track_width": 0.45,
        "is_reversed": False,
        "steering_angle": 0.0,
        "waypoints": [
            [0.75, -0.7],
            [1.0, 0.0],
            [0.7, 0.52],
            [0.58, 0.7],
            [0.48, 0.8],
            [0.15, 0.95],
            [-0.1, 1.0],
            [-0.7, 0.75],
            [-0.9, 0.25],
            [-0.9, -0.55],
        ],
    }


def test_reward():
    params = get_test_params()

    reward = reward_function(params)

    print("test_reward: {}".format(reward))

    assert reward > 0.0


def test_get_target_point():
    result = get_target_point(get_test_params())
    expected = [0.33, 0.86]
    eps = 0.1

    print("get_target_point: x={}, y={}".format(result[0], result[1]))

    assert dist(result, expected) < eps


def test_get_target_steering():
    result = get_target_steering_degree(get_test_params())
    expected = 46
    eps = 1.0

    print("get_target_steering={}".format(result))

    assert abs(result - expected) < eps


def test_angle_mod_360():
    eps = 0.001

    assert abs(-90 - angle_mod_360(270.0)) < eps
    assert abs(-179 - angle_mod_360(181)) < eps
    assert abs(0.01 - angle_mod_360(360.01)) < eps
    assert abs(5 - angle_mod_360(365.0)) < eps
    assert abs(-2 - angle_mod_360(-722)) < eps


def test_upsample():
    params = get_test_params()
    print(repr(up_sample(params["waypoints"], 2)))


def test_score_steer_to_point_ahead():
    params_l_45 = {**get_test_params(), "steering_angle": +45}
    params_l_15 = {**get_test_params(), "steering_angle": +15}
    params_0 = {**get_test_params(), "steering_angle": 0.0}
    params_r_15 = {**get_test_params(), "steering_angle": -15}
    params_r_45 = {**get_test_params(), "steering_angle": -45}

    sc = score_steer_to_point_ahead

    # 0.828, 0.328, 0.078, 0.01, 0.01
    print(
        "Scores: {}, {}, {}, {}, {}".format(
            sc(params_l_45),
            sc(params_l_15),
            sc(params_0),
            sc(params_r_15),
            sc(params_r_45),
        )
    )


def run_tests():
    test_angle_mod_360()
    test_reward()
    test_upsample()
    test_get_target_point()
    test_get_target_steering()
    test_score_steer_to_point_ahead()

    print("All tests successful")


# run_tests()


def get_shortcut_waypoints():
    return [
        [0.63069109, 2.80611932],
        [0.63367125, 2.69079621],
        [0.6467188, 2.57569291],
        [0.66972231, 2.46183988],
        [0.70251506, 2.35022569],
        [0.74487589, 2.24177514],
        [0.79652923, 2.1373277],
        [0.85714459, 2.03761659],
        [0.92633571, 1.94324872],
        [1.00365975, 1.85468625],
        [1.08861721, 1.77223051],
        [1.1806537, 1.69600972],
        [1.27916562, 1.6259728],
        [1.38351227, 1.56189156],
        [1.4930358, 1.50337335],
        [1.60708637, 1.44988322],
        [1.72504192, 1.40077175],
        [1.84630443, 1.35530161],
        [1.97025603, 1.31266612],
        [2.09617545, 1.2719922],
        [2.2231517, 1.23232374],
        [2.35576976, 1.190681],
        [2.48814156, 1.14836059],
        [2.62010372, 1.1049143],
        [2.75155515, 1.06006668],
        [2.88245693, 1.01371411],
        [3.01283929, 0.96594252],
        [3.14278403, 0.91697795],
        [3.27239538, 0.86710616],
        [3.40178871, 0.81664194],
        [3.52534292, 0.76798582],
        [3.64882806, 0.72098717],
        [3.77225054, 0.67657779],
        [3.89565744, 0.63576533],
        [4.01912628, 0.59935302],
        [4.14273194, 0.56802807],
        [4.26652265, 0.54240254],
        [4.390508, 0.52303129],
        [4.5146562, 0.51041311],
        [4.63889641, 0.50498126],
        [4.76312271, 0.50708933],
        [4.88719857, 0.51699788],
        [5.01096146, 0.53486531],
        [5.13422789, 0.56074489],
        [5.25679889, 0.59458804],
        [5.3784661, 0.63625275],
        [5.49901791, 0.68551547],
        [5.61824556, 0.74208505],
        [5.73594876, 0.8056172],
        [5.85194051, 0.87572882],
        [5.96605088, 0.95201138],
        [6.0781297, 1.03404317],
        [6.18804798, 1.12140005],
        [6.29569809, 1.21366463],
        [6.40099292, 1.31043383],
        [6.50386394, 1.41132475],
        [6.60425847, 1.51597899],
        [6.70213638, 1.62406543],
        [6.79746619, 1.73528168],
        [6.89022097, 1.84935431],
        [6.980374, 1.96603801],
        [7.06789434, 2.08511385],
        [7.15274241, 2.20638682],
        [7.23486553, 2.32968268],
        [7.31419351, 2.4548443],
        [7.39063436, 2.58172754],
        [7.46407004, 2.71019664],
        [7.5343525, 2.84011927],
        [7.60129994, 2.9713612],
        [7.6646937, 3.10378064],
        [7.72427579, 3.2372224],
        [7.77974745, 3.37151184],
        [7.83076905, 3.50644891],
        [7.87696157, 3.64180249],
        [7.91791, 3.77730515],
        [7.9531689, 3.91264892],
        [7.98227014, 4.0474821],
        [8.00473301, 4.18140776],
        [8.02007634, 4.31398396],
        [8.02783246, 4.44472614],
        [8.02756242, 4.57311169],
        [8.01887186, 4.69858671],
        [8.00142678, 4.82057488],
        [7.97496831, 4.93848799],
        [7.9393258, 5.05173771],
        [7.89442733, 5.15974804],
        [7.84030706, 5.26196766],
        [7.77710908, 5.35788145],
        [7.7050874, 5.44702069],
        [7.62460227, 5.52897101],
        [7.536113, 5.60337802],
        [7.44016781, 5.66995014],
        [7.33739134, 5.72845868],
        [7.22847048, 5.77873548],
        [7.11413941, 5.82066844],
        [6.99516423, 5.85419554],
        [6.87232807, 5.8792982],
        [6.74641682, 5.89599457],
        [6.61820582, 5.90433369],
        [6.48844757, 5.90439106],
        [6.35786039, 5.89626615],
        [6.22711782, 5.88008231],
        [6.09683868, 5.85598899],
        [5.96757762, 5.82416624],
        [5.83981608, 5.78483111],
        [5.71395379, 5.73824529],
        [5.59030113, 5.68472331],
        [5.46907261, 5.62464036],
        [5.35038212, 5.55843893],
        [5.23424046, 5.48663315],
        [5.12055594, 5.40981015],
        [5.00913994, 5.32862503],
        [4.89972666, 5.24377382],
        [4.79201344, 5.15593375],
        [4.6857631, 5.06560545],
        [4.5807927, 4.97315917],
        [4.48081878, 4.88243357],
        [4.37959748, 4.79420328],
        [4.27684354, 4.70906838],
        [4.17224941, 4.62769566],
        [4.06553767, 4.55071821],
        [3.95644174, 4.47877854],
        [3.84474817, 4.41244104],
        [3.73031118, 4.35215634],
        [3.61306059, 4.29823493],
        [3.49300409, 4.25082828],
        [3.37022468, 4.20991786],
        [3.24487511, 4.17530971],
        [3.1171707, 4.14663361],
        [2.98738247, 4.12334422],
        [2.85585139, 4.10466958],
        [2.72282052, 4.09005797],
        [2.58852158, 4.07896026],
        [2.45315288, 4.07089104],
        [2.31675601, 4.06579649],
        [2.18425079, 4.05787239],
        [2.05356546, 4.04652377],
        [1.9251617, 4.03105575],
        [1.79950825, 4.01084184],
        [1.67721911, 3.98511327],
        [1.55873527, 3.9534865],
        [1.44466638, 3.91541352],
        [1.33564671, 3.8704324],
        [1.23222981, 3.81830074],
        [1.13519251, 3.7586213],
        [1.04519953, 3.69128277],
        [0.96285535, 3.61637202],
        [0.88870748, 3.5341512],
        [0.82324005, 3.44504611],
        [0.76686864, 3.34963169],
        [0.71993756, 3.24861421],
        [0.68271928, 3.1428114],
        [0.65541543, 3.03313123],
        [0.63815905, 2.92055024],
        [0.63069109, 2.80611932],
    ]
