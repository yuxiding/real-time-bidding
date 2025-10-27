def base_reward(clicked: bool, win_price: float, click_value: float = 50.0):
    if clicked:
        return click_value - win_price
    return -win_price


def roi_weighted_reward(clicked: bool, win_price: float, ctr: float, cvr: float, click_value: float = 50.0):
    est_value = ctr * cvr * click_value
    if clicked:
        return est_value - win_price
    return -win_price * (1 + ctr * cvr)


def entropy_regularized_reward(raw_reward: float, policy_entropy: float, entropy_weight: float = 0.01):
    return raw_reward + entropy_weight * policy_entropy


if __name__ == '__main__':
    print("Base clicked reward:", base_reward(True, 2.5))
    print("Base non-clicked reward:", base_reward(False, 2.5))
    print("ROI-weighted clicked:", roi_weighted_reward(True, 2.5, ctr=0.2, cvr=0.1))
    print("Entropy adjusted:", entropy_regularized_reward(30.0, policy_entropy=0.92))
