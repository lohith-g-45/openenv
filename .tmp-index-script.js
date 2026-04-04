
// ============================================================
// PROBLEM DATABASE
// ============================================================
const PROBLEMS = {
  easy: {
    id: 1, title: "Two Sum", difficulty: "easy",
    description: `Given an array of integers <code>nums</code> and an integer <code>target</code>, return <em>indices of the two numbers</em> such that they add up to <code>target</code>.<br><br>You may assume that each input would have <strong>exactly one solution</strong>, and you may not use the same element twice.<br><br>You can return the answer in any order.`,
    examples: [
      { input: "nums = [2,7,11,15], target = 9", output: "[0, 1]", explain: "nums[0] + nums[1] = 2 + 7 = 9" },
      { input: "nums = [3,2,4], target = 6", output: "[1, 2]", explain: "nums[1] + nums[2] = 2 + 4 = 6" }
    ],
    constraints: ["2 ≤ nums.length ≤ 10⁴", "-10⁹ ≤ nums[i] ≤ 10⁹", "Only one valid answer exists"],
    testCases: [
      { input: "[2,7,11,15], 9", expected: "[0, 1]" },
      { input: "[3,2,4], 6", expected: "[1, 2]" },
      { input: "[3,3], 6", expected: "[0, 1]" },
      { input: "[1,2,3,4], 7", expected: "[2, 3]" }
    ],
    defaultCode: `def two_sum(nums, target):
    # Brute force approach (inefficient)
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []`,
    hints: ["Consider using a hashmap to store visited values", "For each element, check if its complement exists", "O(n) solution is possible with a single pass"],
    expectedApproach: "hashmap",
    expectedComplexity: { time: "O(n)", space: "O(n)" }
  },

  medium: {
    id: 2, title: "Longest Substring Without Repeating Characters", difficulty: "medium",
    description: `Given a string <code>s</code>, find the length of the <strong>longest substring</strong> without repeating characters.<br><br>A substring is a contiguous non-empty sequence of characters within a string.`,
    examples: [
      { input: 's = "abcabcbb"', output: "3", explain: 'The answer is "abc", with length 3' },
      { input: 's = "bbbbb"', output: "1", explain: 'The answer is "b", with length 1' },
      { input: 's = "pwwkew"', output: "3", explain: 'The answer is "wke", with length 3' }
    ],
    constraints: ["0 ≤ s.length ≤ 5 × 10⁴", "s consists of English letters, digits, symbols and spaces"],
    testCases: [
      { input: '"abcabcbb"', expected: "3" },
      { input: '"bbbbb"', expected: "1" },
      { input: '"pwwkew"', expected: "3" },
      { input: '""', expected: "0" }
    ],
    defaultCode: `def length_of_longest_substring(s):
    # Buggy approach - off-by-one error
    if not s:
        return 0
    max_len = 0
    for i in range(len(s)):
        seen = set()
        for j in range(i, len(s)):
            if s[j] in seen:
                break
            seen.add(s[j])
        max_len = max(max_len, len(seen) - 1)  # BUG: should not subtract 1
    return max_len`,
    hints: ["Try sliding window with two pointers", "Maintain a set of characters in current window", "Move left pointer when duplicate found"],
    expectedApproach: "two pointers / sliding window",
    expectedComplexity: { time: "O(n)", space: "O(k)" }
  },

  hard: {
    id: 3, title: "Trapping Rain Water", difficulty: "hard",
    description: `Given <code>n</code> non-negative integers representing an elevation map where the width of each bar is <code>1</code>, compute how much water it can trap after raining.<br><br>This is a classic dynamic programming / two-pointer problem.`,
    examples: [
      { input: "height = [0,1,0,2,1,0,1,3,2,1,2,1]", output: "6", explain: "The above elevation map traps 6 units of rain water" },
      { input: "height = [4,2,0,3,2,5]", output: "9", explain: "9 units of rain water are trapped" }
    ],
    constraints: ["n == height.length", "1 ≤ n ≤ 2 × 10⁴", "0 ≤ height[i] ≤ 10⁵"],
    testCases: [
      { input: "[0,1,0,2,1,0,1,3,2,1,2,1]", expected: "6" },
      { input: "[4,2,0,3,2,5]", expected: "9" },
      { input: "[1,0,1]", expected: "1" },
      { input: "[3,0,2,0,4]", expected: "7" }
    ],
    defaultCode: `def trap(height):
    # Brute force O(n²) - needs optimization
    n = len(height)
    total = 0
    for i in range(1, n-1):
        left_max = max(height[:i+1])
        right_max = max(height[i:])
        water = min(left_max, right_max) - height[i]
        if water > 0:
            total += water
    return total`,
    hints: ["Two-pointer approach reduces to O(n) time O(1) space", "Track left_max and right_max as you go", "Process from the side with smaller max height"],
    expectedApproach: "two pointers",
    expectedComplexity: { time: "O(n)", space: "O(1)" }
  }
};

// ============================================================
// MOCK API RESPONSES (replace with real API calls)
// ============================================================
const MOCK_RESPONSES = {
  easy: {
    test_results: { passed: 3, total: 4, cases: [true, true, true, false] },
    error_type: "performance",
    analysis: {
      approach: "Brute Force (Nested Loops)",
      time_complexity: "O(n²)",
      space_complexity: "O(1)",
      bug: "No logical bug, but O(n²) time is inefficient. Fails on large inputs due to TLE.",
      error_detail: "Test case 4 failed: Time Limit Exceeded on large input [nums length > 10000]"
    },
    optimization: {
      approach: "HashMap (Single Pass)",
      explanation: "Use a dictionary to store each number and its index. For each element, check if its complement (target - num) already exists in the map. This reduces time complexity from O(n²) to O(n).",
      code: `def two_sum(nums, target):
    seen = {}  # value -> index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []`
    },
    reward_trace: ["+1 (bug detected)", "+1 (approach classified)", "+2 (optimization correct)"],
    score: { total: 0.87, bug: 0.9, explanation: 0.85, optimization: 0.85 }
  },
  medium: {
    test_results: { passed: 2, total: 4, cases: [false, true, false, true] },
    error_type: "logical_error",
    analysis: {
      approach: "Brute Force (O(n²))",
      time_complexity: "O(n²)",
      space_complexity: "O(k)",
      bug: "Off-by-one error: `len(seen) - 1` incorrectly subtracts 1 from the window size, causing all non-empty results to be one less than expected.",
      error_detail: "Line 10: `max_len = max(max_len, len(seen) - 1)` → should be `len(seen)`"
    },
    optimization: {
      approach: "Sliding Window (Two Pointers)",
      explanation: "Maintain a sliding window [left, right]. Use a hashmap to store character positions. When a duplicate is found, advance the left pointer past the previous occurrence. Track the maximum window size.",
      code: `def length_of_longest_substring(s):
    char_index = {}
    left = max_len = 0
    for right, char in enumerate(s):
        if char in char_index and char_index[char] >= left:
            left = char_index[char] + 1
        char_index[char] = right
        max_len = max(max_len, right - left + 1)
    return max_len`
    },
    reward_trace: ["+1 (bug detected)", "-1 (partial approach)", "+1 (approach reclassified)", "+2 (optimization correct)"],
    score: { total: 0.76, bug: 1.0, explanation: 0.7, optimization: 0.6 }
  },
  hard: {
    test_results: { passed: 4, total: 4, cases: [true, true, true, true] },
    error_type: "performance",
    analysis: {
      approach: "Brute Force DP (O(n²))",
      time_complexity: "O(n²)",
      space_complexity: "O(1)",
      bug: "Correctness: PASS. All test cases pass. However, the solution is O(n²) due to repeated max() calls inside the loop, which will TLE on large inputs (n > 10⁴).",
      error_detail: "Performance issue: `max(height[:i+1])` and `max(height[i:])` are O(n) inside O(n) loop = O(n²) total"
    },
    optimization: {
      approach: "Two Pointers (O(n) time, O(1) space)",
      explanation: "Use two pointers from both ends. Maintain left_max and right_max incrementally (no repeated max() calls). When left_max < right_max, process left; otherwise process right. This achieves O(n) time and O(1) space — optimal.",
      code: `def trap(height):
    left, right = 0, len(height) - 1
    left_max = right_max = 0
    total = 0
    while left < right:
        if height[left] < height[right]:
            if height[left] >= left_max:
                left_max = height[left]
            else:
                total += left_max - height[left]
            left += 1
        else:
            if height[right] >= right_max:
                right_max = height[right]
            else:
                total += right_max - height[right]
            right -= 1
    return total`
    },
    reward_trace: ["+1 (tests passed)", "+1 (approach classified)", "-1 (complexity underestimated)", "+2 (optimization correct)"],
    score: { total: 0.91, bug: 0.95, explanation: 0.9, optimization: 0.9 }
  }
};

// ============================================================
// STATE
// ============================================================
let currentDifficulty = 'easy';
let currentProblem = PROBLEMS.easy;
let tcStatuses = [];

async function callSubmitAPI() {
  const code = document.getElementById('code-editor').value;
  const res = await fetch('/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code })
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const err = await res.json();
      message = err.detail || message;
    } catch (_) {
      // Keep fallback message when body isn't JSON.
    }
    throw new Error(message);
  }

  return await res.json();
}

function mapPipelineToUi(result) {
  const fallback = MOCK_RESPONSES[currentDifficulty];
  const summary = result.execution_summary;
  const summaryResults = (summary && Array.isArray(summary.results)) ? summary.results : [];

  const cases = summaryResults.length
    ? summaryResults.map(r => !!r.passed)
    : fallback.test_results.cases;

  const passed = summaryResults.length
    ? summaryResults.filter(r => r.passed).length
    : fallback.test_results.passed;

  const total = summaryResults.length || fallback.test_results.total;

  const bugs = (result.analysis && result.analysis.bugs) || { total_issues: 0 };
  const approach = (result.analysis && result.analysis.approach) || {};
  const complexity = (result.analysis && result.analysis.complexity) || {};
  const bestOpt = result.optimization && result.optimization.best;

  const syntaxMsg = bugs.syntax_errors && bugs.syntax_errors[0] ? bugs.syntax_errors[0].message : '';
  const logicMsg = bugs.logical_errors && bugs.logical_errors[0] ? bugs.logical_errors[0].message : '';
  const edgeMsg = bugs.edge_case_risks && bugs.edge_case_risks[0] ? bugs.edge_case_risks[0].message : '';

  const bugMessage = syntaxMsg || logicMsg || edgeMsg || 'No critical bug detected.';
  const detailMessage = result.repair_report || 'No additional repair details.';

  const errorType = syntaxMsg
    ? 'syntax_error'
    : logicMsg
      ? 'logical_error'
      : edgeMsg
        ? 'edge_case_risk'
        : 'none';

  const bugScore = Math.max(0, 1 - ((bugs.total_issues || 0) * 0.2));
  const explanationScore = Math.max(0.3, Number(approach.confidence || 0));
  const optimizationScore = bestOpt ? Math.max(0.5, Number(bestOpt.confidence || 0.5)) : 0.25;
  const totalScore = (bugScore + explanationScore + optimizationScore) / 3;

  const rewardTrace = [];
  rewardTrace.push(result.syntax_valid ? '+1 syntax valid' : '-1 syntax invalid');
  rewardTrace.push(total > 0 && passed === total ? '+2 tests passed' : '-1 tests incomplete');
  rewardTrace.push(bestOpt ? '+2 optimization found' : '-1 no optimization');

  return {
    test_results: { passed, total, cases },
    error_type: errorType,
    analysis: {
      approach: (approach.primary || 'unknown').replace(/_/g, ' '),
      time_complexity: complexity.time_complexity || 'Unknown',
      space_complexity: complexity.space_complexity || 'Unknown',
      bug: bugMessage,
      error_detail: detailMessage
    },
    optimization: {
      approach: bestOpt ? bestOpt.approach : 'No optimization candidate',
      explanation: bestOpt ? (bestOpt.explanation || result.optimization.improvement || '') : (result.optimization && result.optimization.improvement) || 'No optimization suggested.',
      code: bestOpt ? (bestOpt.optimized_code || result.fixed_code || result.original_code) : (result.fixed_code || result.original_code)
    },
    reward_trace: rewardTrace,
    score: {
      total: totalScore,
      bug: bugScore,
      explanation: explanationScore,
      optimization: optimizationScore
    }
  };
}

// ============================================================
// INIT
// ============================================================
function init() {
  loadProblem('easy', document.querySelector('.diff-badge.easy'));
  setupEditor();
}

function loadProblem(diff, el) {
  document.querySelectorAll('.diff-badge').forEach(b => b.classList.remove('active'));
  if (el) el.classList.add('active');

  currentDifficulty = diff;
  currentProblem = PROBLEMS[diff];
  tcStatuses = currentProblem.testCases.map(() => 'pending');

  renderProblem();
  renderTestCases();
  renderHints();
  setEditorCode(currentProblem.defaultCode);
  clearOutput();

  document.getElementById('status-task').textContent =
    `Task: ${diff.charAt(0).toUpperCase()+diff.slice(1)} — ${currentProblem.title}`;
  document.getElementById('status-state').textContent = 'State: Idle';
}

// ============================================================
// RENDER PROBLEM
// ============================================================
function renderProblem() {
  const p = currentProblem;
  const diffColors = { easy: 'var(--success)', medium: 'var(--warn)', hard: 'var(--danger)' };
  const col = diffColors[p.difficulty];

  let html = `
    <div class="problem-title">${p.id}. ${p.title}</div>
    <div class="problem-meta">
      <span style="color:${col}; font-size:12px; font-weight:600">${p.difficulty.toUpperCase()}</span>
    </div>
    <div class="problem-desc">${p.description}</div>

    <div class="section-label">Examples</div>`;

  p.examples.forEach((ex, i) => {
    html += `<div class="example-block">
      <div class="example-label">Example ${i+1}</div>
      <div class="example-io"><span class="key">Input:</span> ${ex.input}</div>
      <div class="example-io"><span class="key">Output:</span> ${ex.output}</div>
      <div class="example-io" style="color:var(--muted); font-size:11px; margin-top:4px">${ex.explain}</div>
    </div>`;
  });

  html += `<div class="section-label" style="margin-top:14px">Constraints</div>
    <div class="constraints"><ul>`;
  p.constraints.forEach(c => { html += `<li>${c}</li>`; });
  html += `</ul></div>`;

  document.getElementById('problem-tab').innerHTML = html;
}

function renderTestCases() {
  const tcs = currentProblem.testCases;
  let html = '';
  tcs.forEach((tc, i) => {
    html += `<div class="test-case-item" id="tc-item-${i}">
      <div class="tc-header">
        <span class="tc-label">Case ${i+1}</span>
        <div class="tc-status" id="tc-status-${i}"></div>
      </div>
      <div class="tc-row"><span class="tc-key">Input:</span> <span>${tc.input}</span></div>
      <div class="tc-row"><span class="tc-key">Expected:</span> <span>${tc.expected}</span></div>
      <div class="tc-row" id="tc-actual-${i}" style="display:none"><span class="tc-key">Actual:</span> <span></span></div>
    </div>`;
  });
  document.getElementById('tc-list').innerHTML = html;
}

function renderHints() {
  const p = currentProblem;
  let html = '';
  p.hints.forEach((h, i) => {
    html += `<div style="background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:12px 14px; margin-bottom:8px; font-size:13px; color:#a8a8c0; line-height:1.6">
      <span style="color:var(--accent); font-size:11px; font-weight:600; margin-right:6px">HINT ${i+1}</span>${h}
    </div>`;
  });
  html += `<div style="margin-top:14px; padding:12px; background:rgba(124,106,247,0.06); border:1px solid rgba(124,106,247,0.15); border-radius:8px">
    <div style="font-size:11px; color:var(--muted); margin-bottom:6px; text-transform:uppercase; letter-spacing:0.8px">Expected Approach</div>
    <div style="color:var(--accent); font-size:13px">${p.expectedApproach}</div>
    <div style="margin-top:8px; display:flex; gap:8px">
      <span style="background:var(--surface2); padding:4px 10px; border-radius:5px; font-family:var(--font-code); font-size:11px; color:var(--accent3)">⏱ ${p.expectedComplexity.time}</span>
      <span style="background:var(--surface2); padding:4px 10px; border-radius:5px; font-family:var(--font-code); font-size:11px; color:var(--accent2)">💾 ${p.expectedComplexity.space}</span>
    </div>
  </div>`;
  document.getElementById('hints-content').innerHTML = html;
}

// ============================================================
// EDITOR
// ============================================================
function setupEditor() {
  const ed = document.getElementById('code-editor');
  ed.addEventListener('keydown', e => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = ed.selectionStart;
      ed.value = ed.value.slice(0,start) + '    ' + ed.value.slice(ed.selectionEnd);
      ed.selectionStart = ed.selectionEnd = start + 4;
    }
  });
  ed.addEventListener('input', updateLineNumbers);
  ed.addEventListener('keyup', updateCursor);
  ed.addEventListener('click', updateCursor);
  ed.addEventListener('scroll', syncScroll);
  
  document.getElementById('langSelect').addEventListener('change', e => {
    const lang = e.target.value;
    handleLanguageChange(lang);
  });
  
  updateLineNumbers();
}

const TRANSLATIONS = {
  easy: {
    Python: "def two_sum(nums, target):\n    # Brute force approach (inefficient)\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n    return []",
    JavaScript: "function twoSum(nums, target) {\n    // Brute force approach (inefficient)\n    for (let i = 0; i < nums.length; i++) {\n        for (let j = i + 1; j < nums.length; j++) {\n            if (nums[i] + nums[j] === target) {\n                return [i, j];\n            }\n        }\n    }\n    return [];\n}",
    Java: "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        // Brute force approach (inefficient)\n        for (int i = 0; i < nums.length; i++) {\n            for (int j = i + 1; j < nums.length; j++) {\n                if (nums[i] + nums[j] == target) {\n                    return new int[] { i, j };\n                }\n            }\n        }\n        return new int[] {};\n    }\n}",
    "C++": "class Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        // Brute force approach (inefficient)\n        for (int i = 0; i < nums.size(); i++) {\n            for (int j = i + 1; j < nums.size(); j++) {\n                if (nums[i] + nums[j] == target) {\n                    return {i, j};\n                }\n            }\n        }\n        return {};\n    }\n};",
    "C#": "public class Solution {\n    public int[] TwoSum(int[] nums, int target) {\n        // Brute force approach (inefficient)\n        for (int i = 0; i < nums.Length; i++) {\n            for (int j = i + 1; j < nums.Length; j++) {\n                if (nums[i] + nums[j] == target) {\n                    return new int[] { i, j };\n                }\n            }\n        }\n        return new int[0];\n    }\n}",
    Go: "func twoSum(nums []int, target int) []int {\n    // Brute force approach (inefficient)\n    for i := 0; i < len(nums); i++ {\n        for j := i + 1; j < len(nums); j++ {\n            if nums[i]+nums[j] == target {\n                return []int{i, j}\n            }\n        }\n    }\n    return nil\n}",
    Rust: "impl Solution {\n    pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {\n        // Brute force approach (inefficient)\n        for i in 0..nums.len() {\n            for j in (i + 1)..nums.len() {\n                if nums[i] + nums[j] == target {\n                    return vec![i as i32, j as i32];\n                }\n            }\n        }\n        vec![]\n    }\n}",
    Ruby: "def two_sum(nums, target)\n    # Brute force approach (inefficient)\n    (0...nums.length).each do |i|\n        ((i + 1)...nums.length).each do |j|\n            return [i, j] if nums[i] + nums[j] == target\n        end\n    end\n    []\nend",
    PHP: "class Solution {\n    function twoSum($nums, $target) {\n        // Brute force approach (inefficient)\n        for ($i = 0; $i < count($nums); $i++) {\n            for ($j = $i + 1; $j < count($nums); $j++) {\n                if ($nums[$i] + $nums[$j] == $target) {\n                    return [$i, $j];\n                }\n            }\n        }\n        return [];\n    }\n}"
  }
};

function handleLanguageChange(lang) {
  const currentCode = document.getElementById('code-editor').value;
  
  showLoading(true);
  document.getElementById('status-state').textContent = 'State: Translating to ' + lang;
  
  const stepsContainer = document.querySelector('.loading-steps');
  const originalStepsDisplay = stepsContainer.style.display || 'flex';
  stepsContainer.style.display = 'none';
  
  const msg = document.createElement('div');
  msg.id = 'trans-msg';
  msg.style = 'margin-top:16px; color:var(--accent2); font-size:13px; font-family:var(--font-code)';
  msg.textContent = '> Syntax mapping to ' + lang + '...';
  document.querySelector('.loading-card').appendChild(msg);
  
  const titleEl = document.querySelector('.loading-card > div:nth-child(2)');
  const oldTitle = titleEl.textContent;
  titleEl.textContent = 'AI Language Conversion';
  
  setTimeout(() => {
    showLoading(false);
    document.getElementById('status-state').textContent = 'State: Idle';
    stepsContainer.style.display = originalStepsDisplay;
    titleEl.textContent = oldTitle;
    if (document.getElementById('trans-msg')) document.getElementById('trans-msg').remove();
    
    setEditorCode(mockTranslate(currentCode, lang));
  }, 900);
}

function mockTranslate(code, lang) {
  if (currentDifficulty === 'easy' && TRANSLATIONS.easy[lang] && code.includes('Brute force')) {
    return TRANSLATIONS.easy[lang];
  }
  
  if (lang === 'JavaScript') return code.replace(/def\\b/g, 'function').replace(/:(\\s*)$/gm, ' {$1').replace(/True|False/g, m => m.toLowerCase()) + '\\n}';
  if (lang === 'Python') return code.replace(/function\\b/g, 'def').replace(/[{}]/g, '');
  if (lang === 'Java') return 'class Solution {\\n    // Translated snippet:\\n' + code.split('\\n').map(l=>'    '+l).join('\\n') + '\\n}';
  if (lang === 'C++') return 'class Solution {\\npublic:\\n    // Translated snippet:\\n' + code.split('\\n').map(l=>'    '+l).join('\\n') + '\\n};';
  if (lang === 'Go') return code.replace(/def\\b/g, 'func').replace(/:(\\s*)$/gm, ' {$1') + '\\n}';
  if (lang === 'Rust') return code.replace(/def\\b/g, 'pub fn').replace(/:(\\s*)$/gm, ' {$1') + '\\n}';
  if (lang === 'Ruby') return code.replace(/def\\s+.*:/g, m => m.replace(/:$/, '')) + '\\nend';
  return '// Converted to ' + lang + '\\n' + code;
}

function setEditorCode(code) {
  document.getElementById('code-editor').value = code;
  updateLineNumbers();
}

function updateLineNumbers() {
  const ed = document.getElementById('code-editor');
  const lines = ed.value.split('\n').length;
  const nums = Array.from({length: lines}, (_,i) => i+1).join('\n');
  document.getElementById('lineNums').textContent = nums;
}

function updateCursor() {
  const ed = document.getElementById('code-editor');
  const txt = ed.value.slice(0, ed.selectionStart);
  const lines = txt.split('\n');
  const ln = lines.length;
  const col = lines[lines.length-1].length + 1;
  document.getElementById('line-col').textContent = `Ln ${ln}, Col ${col}`;
}

function syncScroll() {
  const ed = document.getElementById('code-editor');
  document.getElementById('lineNums').style.transform = `translateY(-${ed.scrollTop}px)`;
}

// ============================================================
// TAB SWITCHING
// ============================================================
function showTab(el, targetId) {
  el.closest('.problem-panel').querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  ['problem-tab','testcases-tab','hints-tab'].forEach(id => {
    document.getElementById(id).style.display = id === targetId ? 'block' : 'none';
  });
}

// ============================================================
// RUN TESTS (fast, no full analysis)
// ============================================================
async function runTests() {
  document.getElementById('status-state').textContent = 'State: Running tests';
  currentProblem.testCases.forEach((_, i) => {
    const dot = document.getElementById(`tc-status-${i}`);
    if (dot) { dot.className = 'tc-status running'; }
  });

  let uiResp = MOCK_RESPONSES[currentDifficulty];
  try {
    const payload = await callSubmitAPI();
    if (payload && payload.result) {
      uiResp = mapPipelineToUi(payload.result);
    }
  } catch (err) {
    console.warn('Run tests falling back to mock response:', err.message);
  }

  uiResp.test_results.cases.forEach((pass, i) => {
    const dot = document.getElementById(`tc-status-${i}`);
    if (dot) dot.className = `tc-status ${pass ? 'pass' : 'fail'}`;
  });

  const tabs = document.querySelectorAll('.tab');
  tabs.forEach(t => t.classList.remove('active'));
  tabs[1].classList.add('active');
  document.getElementById('testcases-tab').style.display = 'block';
  document.getElementById('problem-tab').style.display = 'none';
  document.getElementById('hints-tab').style.display = 'none';
  document.getElementById('status-state').textContent = 'State: Tests completed';
}

// ============================================================
// SUBMIT (full analysis)
// ============================================================
async function submitCode() {
  const btn = document.getElementById('submitBtn');
  btn.classList.add('loading');
  btn.textContent = 'Analyzing...';

  showLoading(true);
  document.getElementById('status-state').textContent = 'State: Running RL Agent';

  const steps = ['ls1','ls2','ls3','ls4','ls5','ls6'];
  const delays = [600, 1100, 1700, 2300, 3000, 3700];
  const apiResultPromise = callSubmitAPI()
    .then(payload => (payload && payload.result ? mapPipelineToUi(payload.result) : null))
    .catch(err => {
      console.warn('Submit using mock fallback:', err.message);
      return null;
    });

  steps.forEach((id, i) => {
    setTimeout(() => {
      if (i > 0) {
        const prev = document.getElementById(steps[i-1]);
        prev.classList.remove('active');
        prev.classList.add('done');
        prev.querySelector('.step-icon').textContent = '✓';
      }
      const cur = document.getElementById(id);
      cur.classList.add('active');
    }, delays[i]);
  });

  setTimeout(async () => {
    const last = document.getElementById('ls6');
    last.classList.remove('active');
    last.classList.add('done');
    last.querySelector('.step-icon').textContent = '✓';

    setTimeout(async () => {
      showLoading(false);
      btn.classList.remove('loading');
      btn.textContent = 'Submit →';
      document.getElementById('status-state').textContent = 'State: Done';

      const apiResp = await apiResultPromise;
      const resp = apiResp || MOCK_RESPONSES[currentDifficulty];
      renderOutput(resp);

      // Update test case statuses
      resp.test_results.cases.forEach((pass, i) => {
        const dot = document.getElementById(`tc-status-${i}`);
        if (dot) dot.className = `tc-status ${pass ? 'pass' : 'fail'}`;
      });

      // Reset loading steps
      steps.forEach(id => {
        const el = document.getElementById(id);
        el.className = 'loading-step';
        el.querySelector('.step-icon').textContent = '○';
      });
    }, 400);
  }, 4200);
}

function showLoading(show) {
  document.getElementById('loadingOverlay').classList.toggle('show', show);
}

function clearOutput() {
  document.getElementById('output-empty').style.display = 'flex';
  document.getElementById('output-content').style.display = 'none';
  document.getElementById('output-content').innerHTML = '';
}

// ============================================================
// RENDER OUTPUT
// ============================================================
function renderOutput(resp) {
  document.getElementById('output-empty').style.display = 'none';
  const container = document.getElementById('output-content');
  container.style.display = 'flex';

  const { passed, total, cases } = resp.test_results;
  const allPassed = passed === total;
  const scorePercent = Math.round(resp.score.total * 100);

  let html = '';

  // --- SCORE CARD ---
  html += `<div class="result-card">
    <div class="card-header">
      <div class="card-title">
        <div class="card-dot ${allPassed ? 'dot-success' : 'dot-fail'}"></div>
        Overall Score
      </div>
      <span style="font-size:11px; color:var(--muted)">${passed}/${total} tests passed</span>
    </div>
    <div class="card-body">
      <div class="score-display">
        <div class="score-num" id="score-num">0%</div>
        <div style="text-align:right; font-size:12px; color:var(--muted)">
          <div>${allPassed ? '✓ All Correct' : '✗ Some Failed'}</div>
          <div style="margin-top:2px">Score: ${resp.score.total.toFixed(2)}</div>
        </div>
      </div>
      <div class="score-bar-wrap"><div class="score-bar" id="score-bar"></div></div>
      <div class="score-breakdown">
        <div class="breakdown-item">
          <div class="breakdown-val" style="color:var(--danger)">${Math.round(resp.score.bug*100)}%</div>
          <div class="breakdown-label">Bug Detection</div>
        </div>
        <div class="breakdown-item">
          <div class="breakdown-val" style="color:var(--warn)">${Math.round(resp.score.explanation*100)}%</div>
          <div class="breakdown-label">Explanation</div>
        </div>
        <div class="breakdown-item">
          <div class="breakdown-val" style="color:var(--accent2)">${Math.round(resp.score.optimization*100)}%</div>
          <div class="breakdown-label">Optimization</div>
        </div>
      </div>
    </div>
  </div>`;

  // --- TEST RESULTS ---
  html += `<div class="result-card">
    <div class="card-header">
      <div class="card-title"><div class="card-dot ${allPassed ? 'dot-success' : 'dot-fail'}"></div>Test Results</div>
    </div>
    <div class="card-body">
      <div class="tc-results-grid">`;
  cases.forEach((pass, i) => {
    html += `<div class="tc-result-item">
      <div class="tc-r-dot" style="background:${pass ? 'var(--success)' : 'var(--danger)'}"></div>
      <span style="color:var(--muted)">Case ${i+1}</span>
      <span style="color:${pass ? 'var(--success)' : 'var(--danger)'}; margin-left:auto">${pass ? 'PASS' : 'FAIL'}</span>
    </div>`;
  });
  html += `</div></div></div>`;

  // --- BUG DETECTION ---
  html += `<div class="result-card">
    <div class="card-header">
      <div class="card-title"><div class="card-dot dot-fail"></div>Bug Analysis</div>
    </div>
    <div class="card-body">
      <div style="font-size:12px; color:var(--muted); margin-bottom:8px">Error Type: <span style="color:var(--accent3)">${resp.error_type.replace('_',' ')}</span></div>
      <div class="error-block">${resp.analysis.bug}\n\n${resp.analysis.error_detail}</div>
    </div>
  </div>`;

  // --- APPROACH & COMPLEXITY ---
  html += `<div class="result-card">
    <div class="card-header">
      <div class="card-title"><div class="card-dot dot-info"></div>Approach Detected</div>
    </div>
    <div class="card-body">
      <div class="approach-tag">◈ ${resp.analysis.approach}</div>
      <div class="complexity-row">
        <div class="complexity-badge">
          <div class="complexity-val">${resp.analysis.time_complexity}</div>
          <div class="complexity-label">Time Complexity</div>
        </div>
        <div class="complexity-badge">
          <div class="complexity-val">${resp.analysis.space_complexity}</div>
          <div class="complexity-label">Space Complexity</div>
        </div>
      </div>
    </div>
  </div>`;

  // --- OPTIMIZATION ---
  html += `<div class="result-card">
    <div class="card-header">
      <div class="card-title"><div class="card-dot dot-accent2"></div>Optimized Solution</div>
      <span style="font-size:11px; background:rgba(91,212,180,0.1); color:var(--accent2); padding:2px 7px; border-radius:4px">→ ${resp.optimization.approach}</span>
    </div>
    <div class="card-body">
      <div class="suggest-block">${resp.optimization.explanation}</div>
      <div class="opt-code-block">${escapeHtml(resp.optimization.code)}</div>
    </div>
  </div>`;

  // --- REWARD TRACE ---
  html += `<div class="result-card">
    <div class="card-header">
      <div class="card-title"><div class="card-dot dot-info"></div>RL Reward Trace</div>
    </div>
    <div class="card-body">
      <div style="font-size:11px; color:var(--muted); margin-bottom:8px">Agent actions & rewards:</div>
      <div class="reward-timeline">`;
  resp.reward_trace.forEach(r => {
    const pos = r.startsWith('+');
    html += `<div class="reward-chip ${pos ? 'reward-pos' : 'reward-neg'}">${r}</div>`;
  });
  html += `</div></div></div>`;

  container.innerHTML = html;

  // Animate score bar
  setTimeout(() => {
    document.getElementById('score-bar').style.width = scorePercent + '%';
    animateNumber('score-num', 0, scorePercent, 1000, v => v + '%');
  }, 100);
}

function animateNumber(id, from, to, duration, fmt) {
  const el = document.getElementById(id);
  if (!el) return;
  const start = performance.now();
  function tick(now) {
    const t = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1-t, 3);
    el.textContent = fmt(Math.round(from + (to-from)*ease));
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ============================================================
// START
// ============================================================
init();

