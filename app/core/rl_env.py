class CodeEnv:
    """
    A mock Reinforcement Learning environment for code execution and analysis.
    Mimics standard OpenAI Gym interface with reset() and step().
    """
    
    def __init__(self):
        self.state = {}
        self.task = None
        self.current_step = 0

    def set_task(self, task_id):
        self.task = task_id

    def reset(self):
        self.state = {
            "status": "ready",
            "metrics": {},
            "history": []
        }
        self.current_step = 0
        return self.state

    def step(self, action):
        """
        Executes a single step in the RL environment.
        Returns: observation (state), reward, done, info
        """
        self.current_step += 1
        
        # Track the action in state
        self.state["last_action"] = action
        self.state["metrics"][action] = "completed"
        self.state["history"].append(action)
        
        # Calculate a mock reward
        reward = 1.0  # +1 for each successful analysis step completed
        
        # For this generic loop, we let the external inference driver dictate done state,
        # but normally `done` triggers when goal state is reached or budget exhausted.
        done = False 
        
        info = {
            "step_number": self.current_step,
            "action_executed": action
        }
        
        return self.state, reward, done, info
