# OpenEnv: Intelligent Code Evaluation & Optimization Engine

**OpenEnv** is a state-of-the-art backend engine designed for the next generation of algorithmic learning and high-performance code evaluation. It transforms standard code execution into an intelligent, tutoring-aware environment that not only finds bugs but mathematically proves the absolute best way to solve any algorithmic challenge.

---

## 🚀 Key Features

*   **⚡ Hybrid Intelligence**: Merges deterministic mathematical analysis (AST-based) with the deep reasoning of **Llama-3.3-70B** via the Groq API.
*   **🚑 Heuristic Auto-Repair**: Automatically heals syntax errors (missing colons, brackets) and injects missing edge-case guards (`if not nums: return 0`) before evaluation.
*   **🔮 LLM-Driven Test Oracle**: Dynamically deduces the problem intent and generates 4-5 rigorous LeetCode-style edge cases in JSON format for any submission.
*   **🛡️ Secure Sandbox Execution**: Safely executes user code in a restricted, 5-second max threaded sandbox to prevent infinite loops and protect system resources.
*   **🧮 Mathematical Big-O Prover**: Uses AST inspections and the **Master Theorem** to definitively categorize time and space complexity ($O(n)$, $O(n^2)$, $O(\log n)$, etc.).
*   **🎓 AI-Powered Algorithmic Tutor**: Unlike generic hint systems, our tutor provides deep theoretical walkthroughs, step-by-step logic breakdown, and hands over a perfectly synthesized, optimal Python code block.

---

## 🛠️ Core Engines

1.  **`repair_engine.py`**: The Healer. Fixes syntax and logic structural bugs.
2.  **`execution_engine.py`**: The Sandbox. Secure execution and empirical timing.
3.  **`analysis.py`**: The Mathematician. Static AST analysis and pattern classification.
4.  **`optimization_engine.py`**: The Architect. Rule-based ranking for 14+ algorithmic patterns.
5.  **`llm_manager.py`**: The Brain. Handles LLM integration for synthesis and tutoring.

---

## 🧠 Environment Design

### 📡 State Space
OpenEnv maintains a structured state throughout the evaluation episode:
- **`code`**: The current version of the user's Python solution.
- **`test_results`**: A dictionary mapping test case names to their status (`pass`, `fail`, or `not_run`).
- **`error_type`**: High-level categorization of the detected issue (e.g., `syntax_error`, `logical_error`).
- **`analysis`**: Rich metadata including Big-O complexity, architectural patterns, and AI-generated hints.

### 🎮 Action Space
The environment supports 6 discrete actions to simulate an intelligent tutoring flow:
1.  **`run_tests`**: Executes the code against dynamic test oracles.
2.  **`detect_bug`**: Performs static and dynamic analysis to root-cause errors.
3.  **`classify_approach`**: Categorizes the algorithmic pattern (e.g., Brute Force, DFS).
4.  **`analyze_complexity`**: Calculates the mathematical time and space complexity.
5.  **`suggest_optimization`**: Identifies better algorithmic alternatives.
6.  **`generate_code`**: Synthesizes the final, perfectly optimized solution.

### 🏆 Reward Function
The reward function is designed to incentivize both correctness and a logical diagnostic flow:
- **+1.0**: For any successful analysis action taken in the expected logical sequence.
- **-0.5**: Penalty for taking actions out of order.
- **+5.0**: Bonus for successfully generating a solution that passes all test cases.
- **-1.0**: Penalty if the final generated code fails any test case.

---

## 📅 Tasks & Grading

### 🎯 Available Tasks
1.  **Easy**: Functional repair of basic arithmetic logic.
2.  **Medium**: Reversing strings while maintaining structural integrity.
3.  **Hard**: Optimizing the classic "Two Sum" problem from $O(n^2)$ to $O(n)$ using HashMap lookups.

### ⚖️ Deterministic Grading
Our `grader.py` uses a multi-metric, deterministic scoring system (0.0 to 1.0):
- **30%**: Bug Detection accuracy.
- **30%**: Depth of Analysis and Complexity breakdown.
- **40%**: Final Solution Quality and Optimization.

---

## ⚙️ Installation & Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/lohith-g-45/openenv.git
    cd openenv
    ```

2.  **Setup Virtual Environment**:
    ```bash
    python -m venv venv
    venv\Scripts\activate  # Windows
    source venv/bin/activate  # Mac/Linux
    ```

3.  **Install Dependencies**:
    ```bash
    pip install groq python-dotenv
    ```

4.  **Configure API Key**:
    Create a `.env` file in the root directory and add your Groq API key:
    ```env
    GROQ_API_KEY="your_actual_api_key_here"
    ```

---

## 🚀 How to Run

To run the unified hybrid evaluation pipeline:
```bash
python pipeline.py
```

To run the comprehensive system test:
```bash
python final_test.py
```

---

## ⚖️ License
MIT License. Part of the **Intelligent Code Evaluation and Optimization Environment** Hackathon Project.
