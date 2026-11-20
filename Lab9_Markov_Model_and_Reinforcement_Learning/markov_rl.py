import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)

states = ['Home', 'Office', 'Charging']
transition_matrix = np.array([
    [0.60, 0.30, 0.10],  # from Home
    [0.25, 0.55, 0.20],  # from Office
    [0.50, 0.20, 0.30]   # from Charging
])

def simulate_markov_chain(start_state, steps):
    path = [start_state]
    current = start_state
    for _ in range(steps):
        current = np.random.choice(len(states), p=transition_matrix[current])
        path.append(current)
    return path

path = simulate_markov_chain(start_state=0, steps=200)
counts = np.bincount(path, minlength=len(states))
frequencies = counts / len(path)

print('First 20 simulated states:', [states[i] for i in path[:20]])
for state, frequency in zip(states, frequencies):
    print(f'{state:9}: {frequency:.3f}')

plt.figure(figsize=(7, 4))
plt.bar(states, frequencies, color=['steelblue', 'orange', 'seagreen'])
plt.ylim(0, 1)
plt.ylabel('Fraction of visits')
plt.title('Long-Run Behaviour of the Markov Model')
plt.show()

actions = ['Left', 'Right']
# Reward for taking each action in each state. Rows = states 0..3; columns = Left, Right.
rewards = np.array([[-5, -1], [-2,  1], [ 1, 10], [0, 0]], dtype=float)

def greedy_reward_action(state, reward_table):
    return actions[np.argmax(reward_table[state])]

print('Initial reward table (state 0):', dict(zip(actions, rewards[0])))
print('Greedy choice at state 0:', greedy_reward_action(0, rewards))

changed_rewards = rewards.copy()
changed_rewards[0, 0] = 3  # make Left attractive at state 0
print('After changing Left reward to +3:', dict(zip(actions, changed_rewards[0])))
print('New greedy choice at state 0:', greedy_reward_action(0, changed_rewards))

N_STATES, N_ACTIONS = 5, 2
LEFT, RIGHT = 0, 1

def step(state, action):
    next_state = max(0, state - 1) if action == LEFT else min(N_STATES - 1, state + 1)
    if next_state == 4:
        return next_state, 10, True
    if next_state == 0:
        return next_state, -10, True
    return next_state, -1, False

def train_q_learning(episodes=500, alpha=0.15, gamma=0.9, epsilon=0.1, seed=0):
    rng = np.random.default_rng(seed)
    q_table = np.zeros((N_STATES, N_ACTIONS))
    episode_rewards = []

    for _ in range(episodes):
        state, total_reward, done = 2, 0, False
        while not done:
            if rng.random() < epsilon:
                action = rng.integers(N_ACTIONS)
            else:
                action = int(np.argmax(q_table[state]))
            next_state, reward, done = step(state, action)
            target = reward if done else reward + gamma * np.max(q_table[next_state])
            q_table[state, action] += alpha * (target - q_table[state, action])
            state, total_reward = next_state, total_reward + reward
        episode_rewards.append(total_reward)
    return q_table, np.array(episode_rewards)

q_table, learning_rewards = train_q_learning()
policy = ['Terminal' if s in (0, 4) else actions[np.argmax(q_table[s])] for s in range(N_STATES)]

print('Learned Q-table (Left, Right):')
print(np.round(q_table, 2))
print('Learned policy:', dict(enumerate(policy)))

moving_average = np.convolve(learning_rewards, np.ones(20) / 20, mode='valid')
plt.figure(figsize=(8, 4))
plt.plot(learning_rewards, alpha=0.25, label='Episode reward')
plt.plot(range(19, len(learning_rewards)), moving_average, linewidth=2, label='20-episode average')
plt.xlabel('Episode')
plt.ylabel('Cumulative reward')
plt.title('Q-Learning Curve')
plt.legend()
plt.grid(alpha=0.25)
plt.show()

def evaluate_policy(q_table, trials=100):
    total_rewards, steps_list, successes = [], [], 0
    for _ in range(trials):
        state, total_reward, steps, done = 2, 0, 0, False
        while not done and steps < 20:
            action = int(np.argmax(q_table[state]))
            state, reward, done = step(state, action)
            total_reward += reward
            steps += 1
        successes += state == 4
        total_rewards.append(total_reward)
        steps_list.append(steps)
    return np.mean(total_rewards), np.mean(steps_list), 100 * successes / trials

settings = [('epsilon=0.01', 0.01, 0.9), ('epsilon=0.10', 0.10, 0.9),
            ('epsilon=0.40', 0.40, 0.9), ('gamma=0.20', 0.10, 0.2),
            ('gamma=0.99', 0.10, 0.99)]
results = []

for name, epsilon, gamma in settings:
    q, rewards_run = train_q_learning(epsilon=epsilon, gamma=gamma, seed=10)
    mean_reward, mean_steps, success_rate = evaluate_policy(q)
    final_training_reward = np.mean(rewards_run[-100:])
    results.append((name, final_training_reward, mean_reward, mean_steps, success_rate))

print(f"{'Setting':<15} {'Train reward':>13} {'Eval reward':>12} {'Avg steps':>12} {'Success rate':>14}")
print('-' * 74)
for name, train_reward, avg_reward, avg_steps, rate in results:
    print(f'{name:<15} {train_reward:>13.2f} {avg_reward:>12.2f} {avg_steps:>12.2f} {rate:>13.0f}%')

labels = [row[0] for row in results]
plt.figure(figsize=(8, 4))
plt.bar(labels, [row[1] for row in results], color='mediumpurple')
plt.ylabel('Mean reward in final 100 training episodes')
plt.title('Effect of Epsilon and Gamma on Training Performance')
plt.xticks(rotation=20)
plt.show()

