import numpy as np
import random

# --- Parameters ---
NUM_PARAMS = 2
FREQ_LEVELS = [1, 2, 3]       # example discrete levels
# TODO remove the following to simplify model
DISTANCE_LEVELS = [5, 10, 15]
ANGLE_LEVELS = [30, 60, 90]     
SPEED_LEVELS = [0.5, 1.0, 1.5]

# Actions: 0 = toggle active,
# 1 = freq+, 2 = freq-, 3 = dist+, 4 = dist-,
# 5 = angle+, 6= angle-, 7 = speed+, 8 = speed-
ACTIONS_PER_PARAM = 9
TOTAL_ACTIONS = NUM_PARAMS * ACTIONS_PER_PARAM

# Each parameter looks like: 
# [active, frequency, distance, angle, speed]
# [1, frequency, distance, angle, speed]
#  Would it be possible to simplify t

# Q-Learning hyperparameters
ALPHA = 0.1
GAMMA = 0.9
EPSILON = 0.1
EPISODES = 10000

# --- State and action encoding/decoding ---
def initial_state():
    # Random initial configuration  #TODO start from AutoPi stable configuration
    return np.array([
        [1, FREQ_LEVELS[0], DISTANCE_LEVELS[0], ANGLE_LEVELS[0], SPEED_LEVELS[0]]
        for _ in range(NUM_PARAMS)
    ]).flatten()

def decode_action(action):
    param_idx = action // ACTIONS_PER_PARAM
    sub_action = action % ACTIONS_PER_PARAM
    return param_idx, sub_action

def apply_action(state, action):
    state = state.reshape((NUM_PARAMS, 5)).copy()
    p_idx, sub_act = decode_action(action)

    if sub_act == 0:
        state[p_idx][0] = 1 - state[p_idx][0]  # toggle active
    elif state[p_idx][0] == 1:
        # Only modify if active
        setting_idx = (sub_act - 1) // 2 + 1
        direction = 1 if (sub_act - 1) % 2 == 0 else -1
        setting_array = [FREQ_LEVELS, DISTANCE_LEVELS, ANGLE_LEVELS, SPEED_LEVELS][setting_idx - 1]
        curr_value = state[p_idx][setting_idx]
        new_idx = np.clip(setting_array.index(curr_value) + direction, 0, len(setting_array) - 1)
        state[p_idx][setting_idx] = setting_array[new_idx]

    return state.flatten()

# --- Reward function (simplified simulation) ---
# congestion increases latency,  penalize congestion heavily
# there probably is a delay 



def reward_function(state):
    state = state.reshape((NUM_PARAMS, 5))
    reward = 0
    for param in state:
        active, freq, dist, angle, speed = param
        if active:
            quality = 1.0 - 0.1 * abs(speed - 1.0)  # closer to 1.0 is better
            network_penalty = 0.05 * freq
            reward += quality - network_penalty
    return reward

# --- Q-Table ---
q_table = {}

# --- Training loop ---
for ep in range(EPISODES):
    state = initial_state()
    state_key = tuple(state)
    if state_key not in q_table:
        q_table[state_key] = np.zeros(TOTAL_ACTIONS)

    for step in range(10):  # short episodes
        if random.uniform(0, 1) < EPSILON:
            action = random.randint(0, TOTAL_ACTIONS - 1)
        else:
            action = np.argmax(q_table[state_key])

        next_state = apply_action(state, action)
        next_key = tuple(next_state)

        if next_key not in q_table:
            q_table[next_key] = np.zeros(TOTAL_ACTIONS)

        reward = reward_function(next_state)

        # Q-learning update
        q_table[state_key][action] = q_table[state_key][action] + ALPHA * (
            reward + GAMMA * np.max(q_table[next_key]) - q_table[state_key][action]
        )

        state = next_state
        state_key = next_key

# --- Test sample learned policy ---
test_state = initial_state()
print("Initial:", test_state)

for _ in range(10):
    key = tuple(test_state)
    action = np.argmax(q_table.get(key, np.zeros(TOTAL_ACTIONS)))
    test_state = apply_action(test_state, action)
    print("Action:", decode_action(action), "->", test_state)




"""
Implementation references

OpenAI Spinning Up: https://spinningup.openai.com
Although it focuses more on policy-gradient methods, it gives good context on where Q-learning fits in the broader RL ecosystem.

RL Course by David Silver (DeepMind)
Lectures 4–6 cover model-free methods, including Q-Learning.

Towards Data Science
https://towardsdatascience.com/reinforcement-learning-explained-visually-part-4-q-learning-step-by-step-b65efb731d3e/

---------
=========
---------

Academic references
1. Watkins, C.J.C.H., & Dayan, P. (1992)
   Q-learning: https://link.springer.com/article/10.1007/BF00992698

   
2. Sutton, R. S., & Barto, A. G. (2018)
    Reinforcement Learning: An Introduction (2nd Edition)
    Chapter 6 covers Q-Learning in depth.
    http://incompleteideas.net/book/the-book-2nd.html 
"""