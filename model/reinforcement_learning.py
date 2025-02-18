import numpy as np
import gym
from stable_baselines3 import PPO

class TradingEnv(gym.Env):
    def __init__(self):
        self.action_space = gym.spaces.Discrete(3)
        self.observation_space = gym.spaces.Box(low=-1, high=1, shape=(5,), dtype=np.float32)
        self.state = np.zeros(5)

    def reset(self):
        self.state = np.random.uniform(-1, 1, 5)
        return self.state

    def step(self, action):
        reward = np.random.randn()
        self.state = np.random.uniform(-1, 1, 5)
        return self.state, reward, False, {}

env = TradingEnv()
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)

model.save("rl_model")
